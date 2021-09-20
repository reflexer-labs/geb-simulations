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
# # System Model V3 - Shock test
#
# The purpose of this notebook is to perform shocks of ETH price to test controller parameter stability, without stochastic processes.
#
# For this simulation run, we will be asking the following question: how does the model behave with a eth price shock?
#
# Run simulation with overrides over the default values:
# * 'controller_enabled': [True],
# * 'liquidation_ratio': [1.45],
# * 'interest_rate': [1.03],
# * 'liquidity_demand_enabled': [False],
# * 'arbitrageur_considers_liquidation_ratio': [True],
# * 'liquidity_demand_shock': [False],
# *'eth_price': [lambda run, timestep, df=None: [
#         # Shocks at 14 days; controller turns on at 7 days
#         300,
#         300 if timestep < 24 * 14 else 300 * 1.3, # 30% step, remains for rest of simulation
#         300 * 1.3 if timestep in list(range(24*14, 24*14 + 6, 1)) else 300, # 30% impulse for 6 hours
#         300 if timestep < 24 * 14 else 300 * 0.7, # negative 30% step, remains for rest of simulation
#         300 * 0.7 if timestep in list(range(24*14, 24*14 + 6, 1)) else 300, # negative 30% impulse for 6 hours
#     ][run - 1]],
# * 'liquidity_demand_events': [lambda run, timestep, df=None: 0],
# * 'token_swap_events': [lambda run, timestep, df=None: 0],
# }
#
# In order to test this, configure the following experiment [experiment_shocks.py](experiments/system_model_v3/experiment_shocks.py). Run run this simulation, we create a directory in the ```experiments/system_model_v3``` called ```experiment_shocks/```,and add a ```logs/``` directory inside of it.
#
# Assuming our we have all of the requirements required (run requirements.txt from the ```reflexer/``` root directory to be sure. Assuming our terminal is in the root directory, we run the follow to run the simulation:
#
# ```bash
# python3 -m experiments.system_model_v3.experiment_shocks
# ```
# And our simulation will run. The resulting [run log](experiments/system_model_v3/experiment_shocks/experiment_run_log.md) can be found in the ```experiments/system_model_v3/experiment_shocks/``` directory, along with the simulation results stored as ```experiment_results.hdf5```
#
# Note: The shocks experiment might display errors as the simulations fail under various shock conditions.
#
# Below we will import and examine the simulation results.
#

# %%
# import libraries
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

plt.rcParams['figure.figsize'] = [12, 8]
plt.rcParams['figure.dpi'] = 100 

# %matplotlib inline

# %% [markdown]
# ## Import simulation run data
#

# %%
os.getcwd()

# %%
os.chdir('../../')
os.getcwd()

# %%
experiment_results = 'experiments/system_model_v3/experiment_shocks/experiment_results.hdf5'
experiment_results_keys = []
with pd.HDFStore(experiment_results) as store:
    experiment_results_keys = list(filter(lambda x: "results" in x, store.keys()))
    exceptions_keys = list(filter(lambda x: "exceptions" in x, store.keys()))

# %%
# A list of all experiment result keys
experiment_results_keys

# %%
# Copy a results_ key from the above keys to select the experiment
experiment_results_key = experiment_results_keys[-1]
experiment_timestamp = experiment_results_key.strip('results_')
exceptions_key = 'exceptions_' + experiment_timestamp
experiment_timestamp

# %%
df_raw = pd.read_hdf(experiment_results, experiment_results_key)
df_raw.tail()

# %% [markdown]
# ## Post process
#

# %%
from experiments.system_model_v3.post_process import post_process_results
from experiments.system_model_v3.experiment_shocks import params, SIMULATION_TIMESTEPS

# %%
#params

# %%
# add swept parameters as a column
df = post_process_results(df_raw, params, set_params=['kp', 'ki', 'liquidation_ratio'])
df

# %% [markdown]
# # Simulation Analysis

# %%
df_raw.shape

# %%
df.substep.unique()

# %%
df.subset.unique()

# %%
df.run.unique()

# %%
df.columns


# %%
def plot_fan_chart(df,aggregate_dimension,x, y,lx=False,ly=False,density_hack=True):
    def q10(x):
        return x.quantile(0.1)

    def q20(x):
        return x.quantile(0.2)

    def q30(x):
        return x.quantile(0.3)

    def q40(x):
        return x.quantile(0.4)

    def q60(x):
        return x.quantile(0.6)

    def q70(x):
        return x.quantile(0.7)

    def q80(x):
        return x.quantile(0.8)

    def q90(x):
        return x.quantile(0.9)

    run_count = max(df.run)

    agg_metrics = [q10, q20, q30, q40, 'median', q60, q70, q80, q90]
    agg_df = df.groupby(aggregate_dimension).agg({y: agg_metrics})
    agg_metrics = agg_df.columns.levels[1].values
    agg_df.columns = ['_'.join(col).strip() for col in agg_df.columns.values]
    plt.figure(figsize=(15,9))

    df = agg_df.reset_index()
    lines = plt.plot(df[x], df[f'{y}_median'])
    color = lines[0].get_color()
    if density_hack:
        avg_iqr = []
        for i in range(len(agg_metrics)-1):
            m = (agg_metrics[i], agg_metrics[i+1])
            iqr = df[f'{y}_{m[1]}'] - df[f'{y}_{m[0]}']
            avg_iqr.append(iqr.sum())
        inv_avg_iqr = [1/i for i in avg_iqr]
        norm_avg_iqr = [i/max(inv_avg_iqr) for i in inv_avg_iqr]
        i = 0
        while i<len(agg_metrics)-1:
            m = (agg_metrics[i], agg_metrics[i+1])
            plt.fill_between(df[x], df[f'{y}_{m[0]}'], df[f'{y}_{m[1]}'], alpha=0.8*norm_avg_iqr[i], facecolor=color, edgecolor=None)
            i += 1
    else:
        i = 0
        while i<len(agg_metrics)/2:
            m = (agg_metrics[i], agg_metrics[-1-i])
            plt.fill_between(df[x], df[f'{y}_{m[0]}'], df[f'{y}_{m[1]}'], alpha=0.3, color=color)
            i += 1

    plt.xlabel(x)
    plt.ylabel(y)
    title_text = 'Distribution of ' + y + ' over all of ' + str(run_count) + ' Monte Carlo runs'
    plt.title(title_text)
    plt.legend(['Median', 'Interquantile Ranges'])
    if lx:
        plt.xscale('log')
    if ly:
        plt.yscale('log')


# %%
# calculate errors
df['error'] = df['target_price'] - df['market_price']
df['error_integral'] = df['error'].cumsum()

# %% [markdown]
# ### Generate key plots for analysis

# %%
plot_fan_chart(df,'timestamp','timestamp', 'eth_price',lx=False,ly=False,density_hack=False)
plt.title('ETH price shocks (positive and negative step and impulse; one shock type for each run')


# %%
run = df.query('run==1')
plt.figure(figsize=(15,9))
sns.lineplot(data=run,x="timestep", y="market_price",color='r',label='Market Price in Rai')
sns.lineplot(data=run,x="timestep", y="market_price_twap",color='b',label='Market Price TWAP in Rai')
sns.lineplot(data=run,x="timestep", y="target_price",color='g',label='Redemption Price in Rai')
plt.title('Base case: Stable ETH price response')
plt.legend(loc="upper left")

# %%
run = df.query('run==2').head(500)
sns.lineplot(data=run,x="timestep", y="market_price",color='r',label='Market Price in Rai')
sns.lineplot(data=run,x="timestep", y="market_price_twap",color='b',label='Market Price TWAP in Rai')
sns.lineplot(data=run,x="timestep", y="target_price",color='g',label='Redemption Price in Rai')
plt.title('ETH price 30% step response')
plt.legend(loc="upper left")


# %%
run = df.query('run==3')
sns.lineplot(data=run,x="timestep", y="market_price",color='r',label='Market Price in Rai')
sns.lineplot(data=run,x="timestep", y="market_price_twap",color='b',label='Market Price TWAP in Rai')
sns.lineplot(data=run,x="timestep", y="target_price",color='g',label='Redemption Price in Rai')
plt.title('ETH price 30% impulse response')
plt.legend(loc="upper left")


# %%
sns.lineplot(data=run,x="timestep", y="error",color='r',label='Price Error')
plt.title('Price Error with ETH price 30% impulse response')
plt.legend(loc="upper left")

# %%
sns.lineplot(data=run,x="timestep", y="error_integral",color='r',label='Steady state error')
plt.title('Steady State Error of ETH price 30% impulse response')
plt.legend(loc="upper left")

# %%
run = df.query('run==4')
sns.lineplot(data=run,x="timestep", y="market_price",color='r',label='Market Price in Rai')
sns.lineplot(data=run,x="timestep", y="market_price_twap",color='b',label='Market Price TWAP in Rai')
sns.lineplot(data=run,x="timestep", y="target_price",color='g',label='Redemption Price in Rai')
plt.title('ETH price negative 30% step response')
plt.legend(loc="upper left")


# %%
run = df.query('run==5')
sns.lineplot(data=run,x="timestep", y="market_price",color='r',label='Market Price in Rai')
sns.lineplot(data=run,x="timestep", y="market_price_twap",color='b',label='Market Price TWAP in Rai')
sns.lineplot(data=run,x="timestep", y="target_price",color='g',label='Redemption Price in Rai')
plt.title('ETH price negative 30% impulse response')
plt.legend(loc="upper left")

# %%
plot_fan_chart(df,'timestamp','timestamp', 'principal_debt',lx=False,ly=False,density_hack=True)
plt.title('Reflexer principal debt')


# %%
plot_fan_chart(df,'timestamp','timestamp', 'RAI_balance',lx=False,ly=False,density_hack=True)
plt.title('Secondary market RAI balance')


# %%
plot_fan_chart(df,'timestamp','timestamp', 'ETH_balance',lx=False,ly=False,density_hack=True)
plt.title('Secondary market ETH balance')


# %%
plot_fan_chart(df,'timestamp','timestamp', 'collateralization_ratio',lx=False,ly=False,density_hack=True)
plt.title('Collateralization ratio')


# %% [markdown]
# ## Conclusion
#
# In this notebook we provided an example of a shock test and the types of plots and analysis that can be performed off of it.
