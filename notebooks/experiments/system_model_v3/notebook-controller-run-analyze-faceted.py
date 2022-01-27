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
# # Controller Run and Analyze w/ Faceted Output
#

# %% [markdown]
# ## Setup and Dependencies

# %%
# Set project root folder, to enable importing project files from subdirectories
from pathlib import Path
import os

path = Path().resolve()
root_path = str(path).split('notebooks')[0]
os.chdir(root_path)

# Import all shared dependencies and setup
from shared import *

# %%
import datetime
import time
import warnings
warnings.filterwarnings('ignore')
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
pio.renderers.default = "png"
png_renderer = pio.renderers["png"]
png_renderer.width = 2000
png_renderer.height = 1200


from models.system_model_v3.model.params.init import params
from experiments.system_model_v3.run import run_experiment
from experiments.system_model_v3.configure import generate_params
from experiments.system_model_v3.post_process import post_process_results
from models.constants import RAY 

# %% [markdown]
# ## Simulation Configuration

# %% [markdown]
# ### Length of sims and number of runs

# %%
# Number of timesteps(hours) to run
# Max timesteps is 24 * 30 * 12 = 1 year
SIMULATION_TIMESTEPS = 24 * 30 * 1
#SIMULATION_TIMESTEPS = 24*7

# Number of runs. Each run uses a different simulated ETH dataset
MONTE_CARLO_RUNS = 1

# %% [markdown]
# ### Parameters

# %%
# Set param values. These will override defaults
# Default param values can be found in `models/system_model_v3/model/params/init.py`
params_override = { 
    'debug': [False],
    'eth_trend': [1],# 0:no trend; >0:uptrend; <0:downtrend 
    'liquidity_demand_enabled': [False],
    'liquidity_demand_shock': [False],
    'liquidation_buffer': [2],
    'max_redemption_rate': [50], # used by SAFE owners
    'min_redemption_rate': [-50], # used by SAFE owners
    #'kp': [1e-8, 1e-7],
    #'ki': [5e-15, 5e-14],
    'kp': [5e-8],
    'ki': [0],
    'alpha': [0.999999 * RAY],
    'rate_trader_mean_pct': [3],
    'rate_trader_min_pct': [1],
    'rate_trader_std_pct': [2 * (3-0)],
    'rate_trader_mean_days': [0],
    'rate_trader_min_days': [0],
    'rate_trader_std_days': [2 * (0-0)],
    'uniswap_fee': [0],
    'eth_leverager_target_min_liquidity_ratio': [2.9],
    'eth_leverager_target_max_liquidity_ratio': [2.9]
}
params_update = generate_params(params_override)
params.update(params_update)

# %% [markdown]
# ## Run Simulation

# %%
start = time.time()
df_raw = run_experiment(timesteps=SIMULATION_TIMESTEPS,
               runs=MONTE_CARLO_RUNS, params=params);
df = post_process_results(df_raw, params)
print(f"Run experiment and post-process took {time.time() - start} secs")

# %%
# Optionally, trim results by timestep
#df_trim = df
df_trim = df[df['timestep'] >= 24*7][df['timestep'] <= 24*10]

# %%
df_trim['timestep'].head(3)


# %%
def facet_plot(df, run, facet_col, facet_row):
    """
    Show faceted plots for a singe simulation run
    """
    
    # Just plot first facet_col, facet_row since eth is same for all
    first_col = df[f'{facet_col}'].unique()[0]
    first_row = df[f'{facet_row}'].unique()[0]
    png_renderer.height = 700
    fig = px.line(
        df.query(f'run == {run}')
          .query(f'{facet_col} == {first_col}')
          .query(f'{facet_row} == {first_row}'),
        title=f"ETH/USD",
        x="timestamp",
        y=["eth_price"],
        color_discrete_sequence=['blue'],
        labels={'timestamp': '', 'eth_price': ''}
    )
    fig.update_layout(width=500, height=2000)
    fig.data[0].name = "ETH/USD"
    fig.update_layout(title_x=0.5)
    fig.update_layout(showlegend=False)
    fig.update_layout({'legend_title_text': '', 'legend_x': 0.00, 'legend_y': 1.0})
    fig.update_layout(font={'size': 24})
    fig.update_traces(line=dict(width=2))
    fig.update_layout(yaxis={'title': ''}, xaxis={'title': ''})

    fig.show()

    fig = px.line(
        df.query(f'run == {run}'),
        title=f"RAI/USD",
        x="timestamp",       
        y=["curve_market_price", "market_price", "market_price_twap", "target_price"],
        color_discrete_sequence=['blue', 'purple', 'black', 'red'],
        labels={'timestamp': '', 'target_price': '', 'curve_market_price': '', 'market_price': '', 'market_price_twap': '', 'value': ''},
        facet_col=f'{facet_col}',
        facet_row=f'{facet_row}'
    )
    fig.data[0].name = "RAI/USD Curve"
    fig.data[1].name = "RAI/USD Feed"
    fig.data[2].name = "RAI/USD TWAP"
    fig.data[3].name = "Redemption Price"
    #fig.for_each_annotation(lambda a: a.update(text=a.text.replace("max_redemption_rate", "max rate")))

    fig.update_layout(title_x=0.5)
    fig.update_layout({'legend_title_text': '', 'legend_x': 0.0, 'legend_y': 0})
    fig.update_layout(showlegend=True)
    fig.update_layout(font={'size': 24})
    fig.update_traces(line=dict(width=2))
    fig.update_layout(yaxis={'title': ''}, xaxis={'title': ''})
    fig.show()
    
    fig = px.line(
        df.query(f'run == {run}'),
        title=f"Redemption Rate APY, Note: y-axis set to min/max rate in the run",
        x="timestamp",
        y=['apy'],
        color_discrete_sequence=["blue"],
        labels={'timestamp': '', 'apy': '', 'value': ''},
        facet_col=f'{facet_col}',
        facet_row=f'{facet_row}'
    )

    fig.data[0].name = "Redemption Rate APY"
    fig.for_each_annotation(lambda a: a.update(text=a.text.replace("max_redemption_rate", "max rate")))
     
    min_rate = df.query(f'run == {run}')['apy'].min()
    max_rate = df.query(f'run == {run}')['apy'].max()
    fig.update_yaxes(range=[min_rate, max_rate])
    fig.update_layout(title_x=0.5)
    fig.update_layout({'legend_title_text': '', 'legend_x': 0.00, 'legend_y': 1.0})
    fig.update_layout(showlegend=False)
    fig.update_layout(font={'size':24})
    fig.update_traces(line=dict(width=2))
    fig.update_layout(yaxis={'title': ''}, xaxis={'title': ''})
    fig.show()
    
    fig = px.line(
        df.query(f'run == {run}'),
        title=f"Rate trader total base",
        x="timestamp",       
        y=['rate_trader_total_base'],
        color_discrete_sequence=["green"],
        facet_col=f'{facet_col}',
        facet_row=f'{facet_row}'
    )

    fig.update_layout(title_x=0.5)
    fig.update_layout({'legend_title_text': '', 'legend_x': 0.00, 'legend_y': 1.0})
    fig.update_layout(showlegend=False)
    fig.update_layout(font={'size':24})
    fig.update_traces(line=dict(width=2))
    fig.show()

    fig = px.line(
        df.query(f'run == {run}'),
        title=f"ETH Leverager Collateral",
        x="timestamp",
        y=['eth_leverager_collateral'],
        color_discrete_sequence=['red'],
        facet_col=f'{facet_col}',
        facet_row=f'{facet_row}'
    )

    fig.update_layout(title_x=0.5)
    fig.update_layout({'legend_title_text': '', 'legend_x': 0.00, 'legend_y': 1.0})
    fig.update_layout(showlegend=False)
    fig.update_layout(font={'size':24})
    fig.update_traces(line=dict(width=2))
    fig.show()

    fig = px.line(
        df.query(f'run == {run}'),
        title=f"ETH Leverager C-ratio",
        x="timestamp",        
        y=['eth_leverager_cratio'],
        color_discrete_sequence=['black'],
        facet_col=f'{facet_col}',
        facet_row=f'{facet_row}'
    )

    fig.update_layout(title_x=0.5)
    fig.update_layout({'legend_title_text': '', 'legend_x': 0.00, 'legend_y': 1.0})
    fig.update_layout(showlegend=False)
    fig.update_layout(font={'size':24})
    fig.update_traces(line=dict(width=2))
    fig.show()


# %%
for run in range(1, MONTE_CARLO_RUNS + 1):
    print(f"{run=}")
    facet_plot(df_trim, run, facet_col='ki', facet_row='kp')
