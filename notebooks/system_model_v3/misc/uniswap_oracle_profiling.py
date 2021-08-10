

# %%
from cadCAD_tools.profiling.visualizations import visualize_substep_impact
from cadCAD_tools import profile_run, easy_run
from models.system_model_v3.model.params.init import params
from models.system_model_v3.model.state_variables.init import state_variables
from models.system_model_v3.model.params.init import eth_price_df
import plotly.express as px
from shared import *
from pathlib import Path
import os

path = Path().resolve()
root_path = str(path).split('notebooks')[0]
os.chdir(root_path)
# %%


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
                 1000,
                 system_simulation.N,
                 use_label=False,
                 assign_params=False)

# %%

visualize_substep_impact(df.query('timestep > 950'), relative=False)

# %%
