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
# # System Model V3 - Debt Market Model - Recommended Parameters with Controller On and Off for comparison
#
# The purpose of this notebook is to simulate a single run of the full CDP and APT system model, using a stochastic Ethereum price and liquidity demand process as a driver.
#
#
# We want to run a basic simuluation in order to serve as a sanity check. We want the simulation to have no liquidity shocks, the controller on and off, to show the difference, arbitrageur considers the liquidation ratio, and target price scaling. The market price presented should be stable and should reflect the movement and volatility of the realized sample path of the ETH price.
#
# In order to test this, configure the following experiment [recommended_params.py](https://github.com/BlockScience/reflexer/blob/experiment-analysis/experiments/system_model_v3/recommended_params.py). We use the recommended params with a sweep of controller on/off. Run run this simulation, we create a directory in the ```experiments/system_model_v3``` called ```recommended_params/```,and add a ```logs/``` directory inside of it.
#
# Assuming our we have all of the requirements required (run requirements.txt from the ```reflexer/``` root directory to be sure) and assuming our terminal is in the root directory, we run the follow to run the simulation:
#
# ```bash
# python -m experiments.system_model_v3.recommended_params
# ```
# And our simulation will run. The resulting [run log](https://github.com/BlockScience/reflexer/blob/experiment-analysis/experiments/system_model_v3/recommended_params/experiment_run_log.md)
#  can be found in the ```experiments/system_model_v3/recommended_params/``` directory, along with the simulation results stored as ```experiment_results.hdf5```
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
experiment_results = 'experiments/system_model_v3/recommended_params/experiment_results.hdf5'
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
from experiments.system_model_v3.recommended_params import params, SIMULATION_TIMESTEPS

# %%
df = post_process_results(df_raw, params, set_params=['ki', 'kp', 'liquidation_ratio','controller_enabled'])
df

# %% [markdown]
# # Simulation Analysis

# %%
df.substep.unique()

# %%
df.subset.unique()

# %%
df.columns

# %% [markdown]
# ### Generate key plots for analysis

# %%
df = df.iloc[1:]
controller_off = df.query('controller_enabled==False')
controller_on = df.query('controller_enabled==True')

# calculate erros
controller_off['error'] = controller_off['target_price'] - controller_off['market_price']
controller_off['error_integral'] = controller_off['error'].cumsum()

controller_on['error'] = controller_on['target_price'] - controller_on['market_price']
controller_on['error_integral'] = controller_on['error'].cumsum()

# %%
sns.lineplot(data=controller_on,x="timestamp", y="eth_price",label='Generated Eth price')
ax2 = plt.twinx()
sns.lineplot(data=controller_on,x="timestamp", y="market_price",ax=ax2,color='r',label='Market Price in Rai')
sns.lineplot(data=controller_on,x="timestamp", y="target_price",ax=ax2,color='g',label='Redemption Price in Rai')
plt.title('Generated Eth price vs Simulation Market and Redemption Prices')
plt.legend(loc="upper left")
plt.savefig('experiments/system_model_v3/recommended_params/recommended_params.png')

# %%
controller_on.plot(x='timestamp',y='error',kind='line',title='Error')

# %%
controller_on.plot(x='timestamp',y='error_integral',kind='line',title='Steady state error')

# %%
sns.lineplot(data=controller_on,x="timestamp", y="market_price",color='r',label='Market Price in Rai')
sns.lineplot(data=controller_on,x="timestamp", y="target_price",color='g',label='Redemption Price in Rai')
plt.title('Simulation Market and Redemption Prices')

# %%
sns.lineplot(data=controller_on,x="timestamp", y="target_rate",label='Redemption Rate')
plt.legend(loc="upper left")
plt.show()

# %%
sns.lineplot(data=controller_on,x="timestamp", y="RAI_balance",color='r',label='Rai Issued')
plt.title('RAI balance')


# %%
sns.lineplot(data=controller_on,x="timestamp", y="RAI_balance",color='r',label='Rai Balance in Rai')
sns.lineplot(data=controller_on,x="timestamp", y="principal_debt",color='g',label='CDP total debt (RAI)')
plt.title('RAI balances in CDP/Uniswap')
plt.legend(loc="upper left")
plt.savefig('experiments/system_model_v3/recommended_params/RAI_balances_in_CDPUniswap.png')

# %%
sns.lineplot(data=controller_on,x="timestamp", y="ETH_balance",label='Eth Balance')
plt.legend(loc="upper left")
plt.show()

# %% [markdown]
# ## Controller off

# %%
sns.lineplot(data=controller_off,x="timestamp", y="eth_price",label='Generated Eth price')
ax2 = plt.twinx()
sns.lineplot(data=controller_off,x="timestamp", y="market_price",ax=ax2,color='r',label='Market Price in Rai')
sns.lineplot(data=controller_off,x="timestamp", y="target_price",ax=ax2,color='g',label='Redemption Price in Rai')
plt.title('Controller off')
plt.legend(loc="upper left")
plt.savefig('experiments/system_model_v3/recommended_params/recommended_params_controller_off.png')

# %%
controller_off.plot(x='timestamp',y='error',kind='line',title='Error')

# %%
controller_off.plot(x='timestamp',y='error_integral',kind='line',title='Steady state error')
