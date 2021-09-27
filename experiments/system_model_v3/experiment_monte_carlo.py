import datetime
import os
import numpy as np
import click
import math
import dill

from models.system_model_v3.model.params.init import params
from models.system_model_v3.model.state_variables.init import state_variables
from models.constants import RAY

from experiments.system_model_v3.configure import configure_experiment
from experiments.system_model_v3.run import run_experiment
from experiments.utils import save_to_HDF5, batch, merge_parameter_sweep
from radcad.core import generate_parameter_sweep


# proportional term for the stability controller: units 1/USD
kp_sweep = np.unique(np.append(np.linspace(1e-6/5, 1e-6, 2), np.linspace(1e-6, 5e-6, 2)))
# integral term for the stability controller: units 1/(USD*seconds)
ki_sweep = np.unique(np.append(np.linspace(-1e-9/5, -1e-9, 2), np.linspace(-1e-9, -5e-9, 2)))

sweeps = {
    'controller_enabled': [True, False],
    'kp': kp_sweep,
    #'ki': ki_sweep,
    #'control_period': [3600 * 1, 3600 * 4, 3600 * 7], # seconds; must be multiple of cumulative time
    'control_period': [3600 * 4], # seconds; must be multiple of cumulative time
    'liquidity_demand_shock': [True, False],
}

SIMULATION_TIMESTEPS = 24 * 30 * 1
MONTE_CARLO_RUNS = 1

# Configure sweep and update parameters
params_update, experiment_metrics = configure_experiment(sweeps, timesteps=SIMULATION_TIMESTEPS, runs=MONTE_CARLO_RUNS)
params.update(params_update)

experiment_metrics = f'''

**Parameter subsets are spread across multiple experiments, with the results ID having the same timestamp and an extension for the subset index.**

{experiment_metrics}

```
{sweeps=}
```
'''

# Override parameters
params_override = {
    'liquidation_ratio': [1.45],
    'liquidity_demand_enabled': [True],
    'alpha': [0.999*RAY], # in 1/RAY
    'interest_rate': [1.03],
}
params.update(params_override)

# Experiment details
now = datetime.datetime.now()
dir_path = os.path.dirname(os.path.realpath(__file__))
experiment_folder = __file__.split('.py')[0]
results_id = now.isoformat()

if __name__ == '__main__':
    run_experiment(results_id, experiment_folder, experiment_metrics, timesteps=SIMULATION_TIMESTEPS, runs=MONTE_CARLO_RUNS, params=params, initial_state=state_variables, save_file=True, save_logs=True)
