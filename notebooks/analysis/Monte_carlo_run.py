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
#     display_name: Python (Reflexer)
#     language: python
#     name: python-reflexer
# ---

# %% [raw]
# # System Model V3 - Debt Market Model - Recommended Parameters with Monte Carlo
#
# The purpose of this notebook is to simulate a monte carlo run of the full CDP and APT system model, using a stochastic Ethereum price and liquidity demand process as a driver.
#
#
# We want to run a basic simuluation in order to serve as a sanity check. We want the simulation to have no liquidity shocks, the controller on, arbitrageur considers the liquidation ratio, and target price scaling. The market price presented should be stable and should reflect the movement and volatility of the realized sample path of the ETH price.
#
# In order to test this, configure the following experiment [recommended_params_mc.py](https://github.com/reflexer-labs/geb-simulations/blob/master/experiments/system_model_v3/recommended_params_mc.py). We use the recommended params with a sweep of controller on/off. Run run this simulation, we create a directory in the ```experiments/system_model_v3``` called ```recommended_params_mc/```,and add a ```logs/``` directory inside of it.
#
# Assuming our we have all of the requirements required (run requirements.txt from the ```reflexer/``` root directory to be sure) and assuming our terminal is in the root directory, we run the follow to run the simulation:
#
# ```bash
# python -m experiments.system_model_v3.recommended_params_mc
# ```
# And our simulation will run. The resulting [run log](https://github.com/reflexer-labs/geb-simulations/blob/master/experiments/system_model_v3/recommended_params_mc/experiment_run_log.md)
#  can be found in the ```experiments/system_model_v3/recommended_params_mc/``` directory, along with the simulation results stored as ```experiment_results.hdf5```
#
#
# Below we will import and examine the simulation results.
#

# %%
# import libraries
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

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
experiment_results = 'experiments/system_model_v3/recommended_params_mc/experiment_results.hdf5'
experiment_results_keys = []
with pd.HDFStore(experiment_results) as store:
    experiment_results_keys = list(filter(lambda x: "results" in x, store.keys()))
    exceptions_keys = list(filter(lambda x: "exceptions" in x, store.keys()))

# %%
# A list of all experiment result keys
experiment_results_keys

# %%
# Copy a results_ key from the above keys to select the experiment
experiment_results_key = experiment_results_keys[-1]#'results_2021-02-09T18:46:33.073363' # Or select last result: experiment_results_keys[-1]
experiment_timestamp = experiment_results_key.strip('results_')
exceptions_key = 'exceptions_' + experiment_timestamp
experiment_timestamp

# %%
df_raw = pd.read_hdf(experiment_results, experiment_results_key)
df_raw.tail()

# %% [markdown]
# ## Post process

# %%
from experiments.system_model_v3.post_process import post_process_results
from experiments.system_model_v3.recommended_params_mc import params, SIMULATION_TIMESTEPS

# %%
df = post_process_results(df_raw, params, set_params=['ki', 'kp', 'liquidation_ratio'])
df

# %% [markdown]
# # Simulation Analysis

# %%
df.substep.unique()

# %%
df.run.unique()

# %%
df.subset.unique()

# %%
df.columns

# %%
# remove the first timestep
df = df.iloc[1:]

# %%
# calculate errors
df['error'] = df['target_price'] - df['market_price']
df['error_integral'] = df['error'].cumsum()


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
    plt.figure(figsize=(10,6))

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


# %% [markdown]
# ### Generate key plots for analysis
#
# We use an interquantile range fan chart with a density hack to help understand the true trends of the simulation runs.

# %%
plot_fan_chart(df,'timestamp','timestamp', 'eth_price',lx=False,ly=False,density_hack=True)

# %%
plot_fan_chart(df,'timestamp','timestamp', 'error',lx=False,ly=False,density_hack=True)

# %%
plot_fan_chart(df,'timestamp','timestamp', 'error_integral',lx=False,ly=False,density_hack=True)

# %%
# Redemption Price in Rai
plot_fan_chart(df,'timestamp','timestamp', 'target_price',lx=False, ly=False, density_hack=True)

# %%
# Market Price in Rai
plot_fan_chart(df,'timestamp','timestamp', 'market_price',lx=False,ly=False,density_hack=True)

# %%
# Redemption Rate
plot_fan_chart(df,'timestamp','timestamp', 'target_rate',lx=False,ly=False, density_hack=True)

# %% [markdown]
# ## Conclusion
#
# System simulation appears to be as expected across a series of 5 monte carlo runs.
