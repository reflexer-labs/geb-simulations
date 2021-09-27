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
# ## Grid Search Sensitivity Analysis
#
# Based on an exhausive monte carlo and parameter sweep run previously performed ([run log](../../experiments/system_model_v3/experiment_monte_carlo/experiment_run_log.md) and the [experiment code](../../experiments/system_model_v3/experiment_monte_carlo.py)), postprocessed in the [KPI Notebook](./experiment_notebooks/KPI%20Analysis.ipynb), we will analyze the results and perform sensitivity analysis to illustrate how to examine complex simulation results. 
#

# %%
# Import libraries
import pandas as pd
import matplotlib.pyplot as plt
import pickle as pk

# %matplotlib inline

# %% [markdown]
# # Simulation Analysis

# %%
# load data
df_sensitivity = pd.read_pickle('saved_results/df_sensitivity.pickle')
df_sensitivity.head()

# %%
df_sensitivity.columns

# %%
df_sensitivity.substep.unique()

# %%
df_sensitivity.subset.unique()

# %%
# install cadCAD Machine Search
# cadCAD tools for preparing & analyzing experiments where large-scale machine search for selecting parameters are involved.
# !pip install cadcad_machine_search

# %% [markdown]
# ### Sensitivity Analysis via Machine Search
#
# With Machine Search, we look at the sensitivity of a KPI towards a set of control parameters.
#
# To do so, we fit a decision tree and a random forest classifier to summarize the monte carlo run results. We use the random forest classifier to get feature importance, and the decision tree classifer to visualize the feature importance. We then plot this information to show the KPI's sensativity towards the control parameters.

# %%
from cadcad_machine_search.visualizations import kpi_sensitivity_plot

# Plots the sensitivity of a result dataset towards a KPI.

# Set control parameters for sensitivity analysis
control_params = [
    'ki',
    'kp',
    'control_period',
]

goals = {
    'low_volatility'  : lambda metrics: metrics['kpi_volatility'].mean(),
    'high_stability'  : lambda metrics: metrics['kpi_stability'].mean(),
    'liquidity_threshold': lambda metrics: metrics['kpi_liquidity'].mean(),
}



# %% [markdown]
# #### Controller enabled KPI Sensitivity 

# %%
enabled = df_sensitivity.query(f'controller_enabled == True')
kpi_sensitivity_plot(enabled, goals['low_volatility'], control_params)

# %% [markdown]
# Plot is inclusive.

# %%
kpi_sensitivity_plot(enabled, goals['high_stability'], control_params)

# %%
kpi_sensitivity_plot(enabled, goals['liquidity_threshold'], control_params)

# %% [markdown]
# #### Liquidity Demand Shock KPI Sensitivity  True

# %%
liquidity_demand_shock_true = df_sensitivity.query('liquidity_demand_shock == True')
liquidity_demand_shock_false = df_sensitivity.query('liquidity_demand_shock == False')
kpi_sensitivity_plot(liquidity_demand_shock_true, goals['low_volatility'], control_params)


# %%
kpi_sensitivity_plot(liquidity_demand_shock_true, goals['high_stability'], control_params)

# %%
kpi_sensitivity_plot(liquidity_demand_shock_true, goals['liquidity_threshold'], control_params)

# %% [markdown]
# #### Liquidity Demand Shock KPI Sensitivity - False

# %%
kpi_sensitivity_plot(liquidity_demand_shock_false, goals['low_volatility'], control_params)


# %%
kpi_sensitivity_plot(liquidity_demand_shock_false, goals['high_stability'], control_params)

# %%
kpi_sensitivity_plot(liquidity_demand_shock_false, goals['liquidity_threshold'], control_params)

# %% [markdown]
# #### Liquidity Demand Shock KPI Sensitivity - True

# %%
kpi_sensitivity_plot(liquidity_demand_shock_true, goals['low_volatility'], control_params)


# %%
kpi_sensitivity_plot(liquidity_demand_shock_true, goals['high_stability'], control_params)

# %%
kpi_sensitivity_plot(liquidity_demand_shock_true, goals['liquidity_threshold'], control_params)

# %% [markdown]
# ## Conclusion
