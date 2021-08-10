

# %%
from pathlib import Path
import os

path = Path().resolve()
root_path = str(path).split('notebooks')[0]
os.chdir(root_path)
# %%
from shared import *
import plotly.express as px
from models.system_model_v3.model.params.init import eth_price_df
from models.system_model_v3.model.state_variables.init import state_variables
from models.system_model_v3.model.params.init import params
from cadCAD_tools import profile_run


# %%


state_variables.update({})

params_update = {
    'controller_enabled': [True],
    'kp': [2e-07],  # proportional term for the stability controller: units 1/USD
    # integral term for the stability controller: units 1/(USD*seconds)
    'ki': [-5e-09],
}

params.update(params_update)
SIMULATION_TIMESTEPS = len(eth_price_df) - 1
# SIMULATION_TIMESTEPS = 1000
system_simulation = ConfigWrapper(system_model_v3, T=range(
    SIMULATION_TIMESTEPS), M=params, initial_state=state_variables)
del configs[:]  # Clear any prior configs


df = profile_run(state_variables,
                 params,
                 system_simulation.partial_state_update_blocks,
                 SIMULATION_TIMESTEPS,
                 system_simulation.N,
                 use_label=True,
                 assign_params=False)

# %%
from cadCAD_tools.profiling.visualizations import visualize_elapsed_time_per_ts

visualize_elapsed_time_per_ts(df)
# %%
from cadCAD_tools.profiling.visualizations import visualize_substep_impact

visualize_substep_impact(df.query('timestep > 800'), relative=True)
# %%
visualize_substep_impact(df.query('timestep > 8000'), relative=True)

# %%
visualize_elapsed_time_per_ts(df, relative=True)

# %%
