# -*- coding: utf-8 -*-
# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: -all
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.6.0
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Experiment KPI Analysis

# %% [markdown]
# ## Table of Contents
#
# * [Process KPIs](#Process-KPIs)
# * [Sensitivity Analysis](#Sensitivity-Analysis)
# * [Control Parameter Analysis and Selection](#Control-Parameter-Analysis-and-Selection)

# %%
import pandas as pd
from pandarallel import pandarallel
pandarallel.initialize(progress_bar=False)

# %%
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
# import plotly.io as pio
#pio.renderers.default = "png"
from pprint import pprint

# %%
# Update dataframe display settings
pd.set_option('display.max_columns', 100)
pd.set_option('display.max_rows', 50)
pd.options.plotting.backend = "plotly"

# %% [markdown]
# # Load Dataset

# %%
import os
os.chdir('../../../')
os.getcwd()

# %%
from experiments.system_model_v3.post_process import post_process_results
from experiments.system_model_v3.experiment_monte_carlo import SIMULATION_TIMESTEPS, params
from radcad.core import generate_parameter_sweep

# %%
processed_results = 'experiments/system_model_v3/experiment_monte_carlo/experiment_results.hdf5'

# %%
experiment_results_keys = []
with pd.HDFStore(processed_results) as store:
    experiment_results_keys = list(filter(lambda x: "results" in x, store.keys()))
    exceptions_keys = list(filter(lambda x: "exceptions" in x, store.keys()))
experiment_results_keys

# %%
df_raw = pd.read_hdf(processed_results, key=experiment_results_keys[-1])


# %%
df = post_process_results(df_raw, params, set_params=['kp', 'ki', 'alpha', 'liquidation_ratio', 'controller_enabled', 'control_period', 'liquidity_demand_shock'])

# %%
#df = pd.read_hdf(processed_results, key='results')
#df

# %%
df = df[df['timestep'] >= 1]

# %% [markdown]
# # Process KPIs

# %%
df_kpis = df.copy()

# %%
# Rescale target price according to liquidation ratio, if rescale_target_price set
#cols = ['timestep', 'target_price', 'liquidation_ratio', 'rescale_target_price']
#f = lambda x: (x['target_price'] * x['liquidation_ratio']) if x['rescale_target_price'] and x['timestep'] > 0 else x['target_price']
#df_kpis['target_price_scaled'] = df_kpis[cols].parallel_apply(f, axis=1)
#df_kpis['target_price_scaled'].head(10)

# %% [markdown]
# ## Stability

# %% [markdown]
# **Stability** threshold of system: defined as the maximum value for relative frequency of simulation runs that are unstable. Unstable is measured as fraction of runs where:
#   - market price runs to infinity/zero (e.g. upper bound 10xPI; lower bound 0.10xPI if initial price is PI);
#   - redemption price runs to infinity/zero (e.g. upper bound 10xPI; lower bound 0.10xPI if initial price is PI);
#   - Uniswap liquidity (RAI reserve) runs to zero;
#   - CDP position (total ETH collateral) runs to infinity/zero.

# %%
# Get initial target price for calculations
initial_target_price = df_kpis['target_price'].iloc[0]
initial_target_price

# %%
# Get decile stats. for system states, to set KPI thresholds
df_kpis[['market_price', 'target_price', 'RAI_balance', 'eth_collateral']].describe([0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.90])

# %%
df_stability = df_kpis.groupby(['subset'])

# Calculate aggregate values for each subset
df_stability = df_stability.agg({
    'market_price': ['min', 'max'],
    'target_price': ['min', 'max'],
    'RAI_balance': ['min', 'max'],
    'eth_collateral': ['min', 'max'],
})
df_stability.columns = [
    'market_price_min', 'market_price_max',
    'target_price_min', 'target_price_max',
    'RAI_balance_min', 'RAI_balance_max',
    'eth_collateral_min', 'eth_collateral_max'
]
df_stability = df_stability.reset_index()

# Set stability KPI for market price
df_stability['stability_market_price'] = df_stability \
    .apply(lambda x: x['market_price_min'] >= 0.1*initial_target_price and x['market_price_max'] <= 10*initial_target_price, axis=1)

# Set stability KPI for target price
df_stability['stability_target_price'] = df_stability \
    .apply(lambda x: x['target_price_min'] >= 0.1*initial_target_price and x['target_price_max'] <= 10*initial_target_price, axis=1)

# Set stability KPI for Uniswap RAI balance
# NOTE: threshold set according to decile stats.
df_stability['stability_uniswap_liquidity'] = df_stability \
    .apply(lambda x: x['RAI_balance_min'] >= 50e3, axis=1)

# Set stability KPI for CDP ETH collateral
# NOTE: threshold set according to decile stats.
df_stability['stability_cdp_system'] = df_stability \
    .apply(lambda x: x['eth_collateral_min'] > 0, axis=1)

# Calculate aggregate stability KPI
df_stability['kpi_stability'] = df_stability \
    .apply(lambda x: ( \
        x.stability_cdp_system == True and \
        x.stability_uniswap_liquidity == True and \
        x.stability_market_price == True and \
        x.stability_target_price == True) \
        , axis=1)

# Get all subsets where stability KPI is met
df_stability.query('kpi_stability == True')

# %%
df_stability.query('kpi_stability == False')

# %%
df_stability.columns

# %% [markdown]
# ## Volatility

# %% [markdown]
# **Volatility** threshold of market price: defined as the maximum value for the **standard deviation** computed. Defined relative to ETH price volatility. Definition: ratio of RAI price volatility / ETH price volatility is not to exceed 0.5.
#   - over simulation period;
#   - as moving average with 10-day window.

# %%
df_volatility_grouped = df_kpis.groupby(['subset'])

# Calculate aggregate values for each subset
df_volatility_grouped = df_volatility_grouped.agg({'market_price': ['std'], 'eth_price': ['std']})
df_volatility_grouped.columns = ['market_price_std', 'eth_price_std']
df_volatility_grouped = df_volatility_grouped.reset_index()

# Set volatility ratio for each subset 
df_volatility_grouped['volatility_ratio_simulation'] = \
    df_volatility_grouped[['subset', 'market_price_std', 'eth_price_std']] \
    .apply(lambda x: x['market_price_std'] / x['eth_price_std'], axis=1)

# Calculate per subset volatility KPI based on ratio
df_volatility_grouped['kpi_volatility_simulation'] = df_volatility_grouped.apply(lambda x: x['volatility_ratio_simulation'] <= 0.5, axis=1)

# Get all subsets where subset volatility KPI is met
df_volatility_grouped.query('kpi_volatility_simulation == True')

# %%
df_volatility_series = pd.DataFrame()
group = df_kpis.groupby(['subset', 'run'])

# Calculate rolling average standard deviation for each subset/run combination
df_volatility_series['market_price_moving_average_std'] = group['market_price'].rolling(24*10, 1).std()
df_volatility_series['eth_price_moving_average_std'] = group['eth_price'].rolling(24*10, 1).std()
df_volatility_series

# %%
# Calculate volatility ratio for each subset/run combination
f = lambda x: x['market_price_moving_average_std'] / x['eth_price_moving_average_std']
df_volatility_series['volatility_ratio_window'] = df_volatility_series.parallel_apply(f, axis=1)
df_volatility_series.head(5)

# %%
# Group by subset and calculate volatility ratio for each subset as the mean
f = lambda x: x['volatility_ratio_window'] != x['volatility_ratio_window'] or x['volatility_ratio_window'] <= 0.5
df_volatility_series['volatility_window_series'] = df_volatility_series.parallel_apply(f, axis=1)
df_volatility_series['volatility_window_mean'] = (df_volatility_series.groupby(['subset'])
                                                                           ['volatility_window_series']
                                                                          .transform(lambda x: x.mean()))
df_volatility_series.head(5)

# %%
# Check volatility stats
df_volatility_series['volatility_window_mean'].describe()

# %%
# Set volatility KPI threshold based on volatility stats
df_volatility_series['kpi_volatility_window'] = df_volatility_series.groupby(['subset'])['volatility_window_mean'].transform(lambda x: x > 0.98)
df_volatility_series

# %%
# Get all subsets where window volatility KPI is met
df_volatility_series.query('kpi_volatility_window == True')

# %%
# Count window volatility KPI values (True/False)
df_volatility_series['kpi_volatility_window'].value_counts()

# %% [markdown]
# ## Merge KPI dataframes

# %%
# Select columns to drop from final dataset
cols_to_drop = {
    'volatility_window_series',
    'market_price_moving_average_std',
    'eth_price_moving_average_std',
    'index'
}

# Select column to groupby
index_cols = ['subset']
# Set dataframes to join
dfs_to_join = [df_volatility_grouped, df_volatility_series, df_stability]

# Join dataframes, dropping columns and re-setting the index
for i, df_to_join in enumerate(dfs_to_join):
    _df = df_to_join.reset_index()
    remaining_cols = list(set(_df.columns) - cols_to_drop)
    _df = (_df.reset_index()
              .loc[:, remaining_cols]
              .groupby(index_cols)
              .first()
          )
    dfs_to_join[i] = _df

df_kpis = (dfs_to_join[0].join(dfs_to_join[1], how='inner')
                         .join(dfs_to_join[2], how='inner')
          )

# %%
# Calculate volatility KPI
df_kpis['kpi_volatility'] = df_kpis.apply(lambda x: x['kpi_volatility_simulation'] and x['kpi_volatility_window'], axis=1)

# %%
# Get all subsets where volatility KPI is not met
df_kpis.query('kpi_volatility == False and kpi_stability == False')

# %% [markdown]
# ## Liquidity

# %% [markdown]
# **Liquidity** threshold of secondary market: defined as the maximum slippage value below which the controller is allowed to operate.
# * __NB__: Threshold value will be determined by experimental outcomes, e.g. sample mean of the Monte Carlo outcomes of the slippage value when the system becomes unstable. Would like variance/std deviation of the Monte Carlo slippage series to be small (tight estimate), but can report both mean and variance as part of recommendations

# %%
# Placeholder value, which must be determined
critical_liquidity_threshold = None

# %%
# To calculate liquidity threshold, create a copy of the timeseries dataframe with market slippage, and merge with KPI dataframe
df_liquidity = df[['subset', 'run', 'timestep', 'market_slippage']].copy()
df_liquidity = pd.merge(df_liquidity, df_kpis, how='inner', on=['subset', 'run'])
# Take the absolute value of market slippage (swap direction in or out of the liquidity pool)
df_liquidity['market_slippage_abs'] = df_liquidity['market_slippage'].transform(lambda x: abs(x))
df_liquidity

# %%
# Check absolute value market slippage decile stats
df_liquidity.query('subset == 0')['market_slippage_abs'].describe([0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.90])

# %%
# For each subset, calculate the 90th percentile market slippage
df_liquidity['market_slippage_percentile'] = df_liquidity.groupby(['subset'])['market_slippage'].transform(lambda x: x.quantile(.90))
df_liquidity

# %%
# %%capture
# Select all subsets that failed the volatility and stability KPIs
# NOTE: updated to just use stability KPI and not volatility KPI to not over-tune
df_liquidity_failed = df_liquidity.query('kpi_stability == False')
df_liquidity_failed['market_slippage_percentile_mean'] = df_liquidity_failed.groupby(['subset'])['market_slippage_percentile'].transform(lambda x: x.mean())

# %%
# Get the mean liquidity threshold of all failed runs
critical_liquidity_threshold = df_liquidity_failed['market_slippage_percentile_mean'].mean()
critical_liquidity_threshold

# %%
# Calculate liquidity KPI based on critical liquidity threshold found above
df_liquidity_grouped = df_liquidity.groupby(['subset']).mean()
df_liquidity_grouped = df_liquidity_grouped.reset_index()
df_liquidity_grouped['kpi_liquidity'] = df_liquidity_grouped.apply(lambda x: x['market_slippage_percentile'] <= critical_liquidity_threshold, axis=1)
df_liquidity_grouped

# %%
# Save interim results
df_liquidity_grouped.to_pickle('experiments/system_model_v3/experiment_monte_carlo/df_liquidity_grouped.pickle')

# %%
# Aggregate KPIs per subset
df_kpis = df_liquidity_grouped[['subset', 'run', 'kpi_stability', 'kpi_volatility', 'kpi_liquidity']]
df_kpis = df_kpis.groupby(['subset']).first()

# %%
print(f'''
{round(df_kpis.query('kpi_stability == True and kpi_volatility == True and kpi_liquidity == True').count().iloc[0]*100/df_kpis.count().iloc[0])}% successful KPIs
''')

# %%

# %% [markdown]
# ## Save KPI Results

# %%
# Save interim results
df_kpis.to_pickle('experiments/system_model_v3/experiment_monte_carlo/df_kpis.pickle')

# %%
# Load interim results
df_kpis = pd.read_pickle('experiments/system_model_v3/experiment_monte_carlo/df_kpis.pickle')

# %% [markdown]
# # Sensitivity Analysis

# %%
# Merge KPI dataframe with timeseries dataframe, and grouped liquidity dataframe,
# including volatility_ratio_simulation and volatility_ratio_window for sensitivity analysis later
df_sensitivity = pd.merge(df, df_kpis, on=['run','subset'], how='inner')
df_sensitivity = pd.merge(df_sensitivity, df_liquidity_grouped[[
    'run',
    'subset',
    'volatility_ratio_simulation',
    'volatility_ratio_window'
]], on=['run','subset'], how='inner')
df_sensitivity.head(1)

# %%
df_sensitivity = df_sensitivity.reset_index()

# %%
# Save interim results
df_sensitivity.to_pickle('experiments/system_model_v3/experiment_monte_carlo/df_sensitivity.pickle')

# %%
# Set control parameters for sensitivity analysis
control_params = [
    'ki',
    'kp',
    'control_period',
]

# %%
from cadcad_machine_search.visualizations import kpi_sensitivity_plot

goals = {
    'low_volatility'  : lambda metrics: metrics['kpi_volatility'].mean(),
    'high_stability'  : lambda metrics: metrics['kpi_stability'].mean(),
    'liquidity_threshold': lambda metrics: metrics['kpi_liquidity'].mean(),
}

# TODO: configure visualizations for analysis
for scenario in df_sensitivity['controller_enabled'].unique():
    _df = df_sensitivity.query(f'controller_enabled == {scenario}')
    for goal in goals:
        kpi_sensitivity_plot(_df, goals[goal], control_params)


# %%
enabled = df_sensitivity.query(f'controller_enabled == True')
for goal in goals:
    kpi_sensitivity_plot(enabled, goals[goal], control_params)


# %%
for scenario in df_sensitivity['liquidity_demand_shock'].unique():
    _df = df_sensitivity.query(f'liquidity_demand_shock == {scenario}')
    for goal in goals:
        kpi_sensitivity_plot(_df, goals[goal], control_params)

# %%
critical_liquidity_threshold

# %%
from cadcad_machine_search.visualizations import plot_goal_ternary

# danlessa notes:
# 1. Make sure that the KPIs they are well behaved: eg: no NaNs
# 2. Be aware of division by zero on the goals
# 3. KPIs must transform a (N_s x N_t) array into a (N_s, 1) vector 
#   - N_s: number of 'experiments' (N_sweeps + N_mc)

kpis = {
    'volatility_simulation'        : lambda df: df['volatility_ratio_simulation'].max(),
    'volatility_window_mean'       : lambda df: df['volatility_ratio_window'].mean(),
    'market_price_max'             : lambda df: df['market_price'].max(),
    'market_price_min'             : lambda df: df['market_price'].min(),
    'redemption_price_max'         : lambda df: df['target_price'].max(),
    'redemption_price_min'         : lambda df: df['target_price'].min(),
    'rai_balance_uniswap_min'      : lambda df: df['RAI_balance'].min(),
    'cdp_collateral_balance_min'   : lambda df: df['eth_collateral'].min(),
    #'price_change_percentile_mean' : lambda df: critical_liquidity_threshold # This is ill condionated! df -> float
}

from typing import Callable, Dict, List


def low_volatility_goal(metrics: Dict[str, List[float]]) -> float:
    utility = metrics['volatility_simulation']     
    #utility += metrics['price_change_percentile_mean']
    utility *= -1.0
    return utility
    

def high_stability_goal(metrics: Dict[str, List[float]]) -> float:
    # Note: I've changed the 1/x terms to -1 terms due to div by zero problems
    utility = metrics['market_price_max']
    utility -= metrics['market_price_min']
    utility -= metrics['redemption_price_max']
    utility -= metrics['redemption_price_min']
    utility -= metrics['rai_balance_uniswap_min']
    utility -= metrics['cdp_collateral_balance_min']
    utility *= -1.0
    return utility

def liquidity_goal(metrics: Dict[str, List[float]]) -> float:
    # danlessa note: price_change_percentile_mean seems to be ill-condionated
    # utility = -metrics['price_change_percentile_mean']
    utility = -metrics['market_price_min'] # Just for debugging
    return utility


goals = {
    'low_volatility': low_volatility_goal,
    'high_stability':  high_stability_goal,
    'liquidity': liquidity_goal,
    'combined': lambda goals: goals[0] + goals[1] + goals[2]
}


for scenario in df_sensitivity['controller_enabled'].unique():
    print("---")
    print(scenario)
    _df = df_sensitivity.query(f'controller_enabled == {scenario}')
    plot_goal_ternary(_df, kpis, goals, control_params)
    print("---")


# %% [markdown]
# # Control Parameter Analysis and Selection

# %%
df_liquidity_grouped = pd.read_pickle('experiments/system_model_v3/experiment_monte_carlo/df_liquidity_grouped.pickle')

# %%
# Create analysis dataframe, using liquidity grouped dataframe and sensitivity dataframe
df_sensitivity = pd.read_pickle('experiments/system_model_v3/experiment_monte_carlo/df_sensitivity.pickle')
df_analysis = df_sensitivity.groupby(['subset']).mean()
# Keep the difference of the columns
keep_cols = df_liquidity_grouped.columns.difference(df_analysis.columns)
df_analysis = pd.merge(df_analysis, df_liquidity_grouped[keep_cols], on=['subset'], how='inner')

# %%
# Select all runs that passed the KPIs
df_analysis = df_analysis.query('kpi_stability == True and kpi_volatility == True and kpi_liquidity == True')

df_analysis

# %%
# Save interim results
df_analysis.to_pickle('experiments/system_model_v3/experiment_monte_carlo/df_analysis.pickle')


# %% [markdown]
# # Subset KPI Ranking

# %%
def map_params(df, params, set_params):
    '''
    Sets the parameters for each subset in the dataframe
    '''
    param_sweep = generate_parameter_sweep(params)
    param_sweep = [{param: subset[param] for param in set_params} for subset in param_sweep]
    for subset_index in df['subset'].unique():
        for (key, value) in param_sweep[subset_index].items():
            df.loc[df.eval(f'subset == {subset_index}'), key] = value


# %%
# Select which parameters to set in the dataframe for each subset
set_params = [
    'kp',
    'ki',
    'alpha',
    'liquidation_ratio',
    'controller_enabled',
    'control_period',
    'liquidity_demand_shock',
]


# %%
# Assign parameters to subsets
map_params(df_analysis, params, set_params)

# %%
# Select subsets where the controller was enabled
df_controller_enabled = df_analysis.query('controller_enabled == True')

# %% [markdown]
# ## Volatility KPI Ranking
#
# Rank the subsets that meet all KPIs according to the volatility KPI measure.

# %%
# %%capture
lambda_volatility_measure = lambda x: -0.5 * (x + critical_liquidity_threshold)
df_controller_enabled['kpi_volatility_measure'] = df_controller_enabled['volatility_ratio_simulation'].apply(lambda_volatility_measure)

# %%
df_volatility_measure = df_controller_enabled.groupby(['subset']).agg({
    'kpi_volatility_measure': lambda x: x.mean(skipna=True),
    'kp': 'first',
    'ki': 'first',
    'control_period': 'first',
}).sort_values(by='kpi_volatility_measure', kind="mergesort", ascending=False)
df_volatility_measure

# %%
df[df['subset'].isin(list(df_volatility_measure.index)[:10])].query('run == 1').plot(
    title='Market price of top 10 subsets ranked according to volatility KPI measure',
    x='timestamp', y='market_price', color='subset'
)

# %% [markdown]
# ## Stability KPI Ranking
#
# Rank the subsets that meet all KPIs according to the stability KPI measure.

# %%
# %%capture
lambda_stability_measure = lambda x: -(1/6) * ( x['market_price_max'] + 
                    1 / x['market_price_min'] + x['target_price_max'] +
                    1 / x['target_price_min'] + 1 / x['RAI_balance_min'] +
                    1 / x['eth_collateral_min'] )

df_controller_enabled['kpi_stability_measure'] = df_controller_enabled.apply(lambda_stability_measure, axis=1)

# %%
df_stability_measure = df_controller_enabled.groupby(['subset']).agg({
    'kpi_stability_measure': lambda x: x.mean(skipna=True),
    'kp': 'first',
    'ki': 'first',
    'alpha': 'first',
    'control_period': 'first',
}).sort_values(by='kpi_stability_measure', kind="mergesort", ascending=False)
df_stability_measure

# %%
df[df['subset'].isin(list(df_stability_measure.index)[:10])].query('run == 1').plot(
    title='Market price of top 10 subsets ranked according to stability KPI measure',
    x='timestamp', y='market_price', color='subset'
)

# %% [markdown]
# ## Liquidity KPI Ranking
#
# Rank the subsets that meet all KPIs according to the liquidity KPI measure.

# %%
df_liquidity_measure = df_controller_enabled.groupby(['subset']).agg({
    'market_slippage_percentile': lambda x: x.mean(skipna=True),
    'kp': 'first',
    'ki': 'first',
    'alpha': 'first',
    'control_period': 'first',
}).sort_values(by='market_slippage_percentile', kind="mergesort")
df_liquidity_measure

# %%
df[df['subset'].isin(list(df_liquidity_measure.index)[:10])].query('run == 1').plot(
    title='Market price of top 10 subsets ranked according to liquidity KPI measure',
    x='timestamp', y='market_price', color='subset'
)

# %% [markdown]
# ## Aggregate KPI rankings

# %%
# Find intersection of top 25 of each KPI measure
subset_kpi_indexes = df_stability_measure.index[:25].intersection(df_liquidity_measure.index[:25]).intersection(df_volatility_measure.index[:25])
subset_kpi_selection = list(subset_kpi_indexes)
subset_kpi_selection

# %%
df_selection = df_controller_enabled[df_controller_enabled['subset'].isin(subset_kpi_selection)]
df_selection

# %%
# Select all dataframes with the control_period less than 25200
df_selection = df_selection.query('control_period < 25200')
df_selection

# %%
df_selection_timeseries = df[df['subset'].isin(list(df_selection.index))]

# %% [markdown]
# ## Subset 4 time series

# %%
df_controller_enabled.query('subset == 4')[['kp', 'ki', 'control_period', 'alpha']]

# %%
df_selection_timeseries.query('subset == 4').plot(x='timestamp', y='market_price', color='run')

# %%
df_selection_timeseries.query('subset == 4').plot(x='timestamp', y=['market_price_twap'], color='run')

# %%
df_selection_timeseries.query('subset == 4').plot(x='timestamp', y=['target_price'], color='run')

# %% [markdown]
# ## Conclusion
