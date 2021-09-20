import datetime
import os
import numpy as np

from models.system_model_v3.model.params.init import params
from models.system_model_v3.model.state_variables.init import state_variables

from experiments.system_model_v3.configure import configure_experiment
from experiments.system_model_v3.run import run_experiment
from experiments.utils import save_to_HDF5

from models.system_model_v3.model.state_variables import liquidity

# proportional term for the stability controller: units 1/USD
kp_sweep = np.unique(np.append(np.linspace(1e-6/5, 1e-6, 3), np.linspace(1e-6, 5e-6, 3)))
# integral term for the stability controller: units 1/(USD*seconds)
ki_sweep = np.unique(np.append(np.linspace(-1e-9/5, -1e-9, 3), np.linspace(-1e-9, -5e-9, 3)))

kp_sweep = [5e-7, 1e-7, 5e-8, 1e-08]
# integral term for the stability controller: units 1/(USD*seconds)
ki_sweep = [-1e-7, -5e-8, -1e-8, 1e-9, 5e-8, 1e-8]


sweeps = {
    'kp': kp_sweep,
    'ki': ki_sweep,
}

SIMULATION_TIMESTEPS = int(24 * 30 * 1.5) # Updated to two month horizon for shock tests
MONTE_CARLO_RUNS = 5 # Each MC run will map to different shock

# Configure sweep and update parameters
params_update, experiment_metrics = configure_experiment(sweeps, timesteps=SIMULATION_TIMESTEPS, runs=MONTE_CARLO_RUNS)
params.update(params_update)

experiment_metrics = f'''
{experiment_metrics}

```
{kp_sweep=}
{ki_sweep=}
```
'''

# Override parameters
params_override = {
    'controller_enabled': [True],
    'liquidation_ratio': [1.45],
    'interest_rate': [1.03],
    'liquidity_demand_enabled': [False],
    'liquidity_demand_shock': [False],
    'eth_price': [lambda run, timestep, df=None: [
        # Shocks at 14 days; controller turns on at 7 days
        300,
        300 if timestep < 24 * 14 else 300 * 1.3, # 30% step, remains for rest of simulation
        300 * 1.3 if timestep in list(range(24*14, 24*14 + 6, 1)) else 300, # 30% impulse for 6 hours
        300 if timestep < 24 * 14 else 300 * 0.7, # negative 30% step, remains for rest of simulation
        300 * 0.7 if timestep in list(range(24*14, 24*14 + 6, 1)) else 300, # negative 30% impulse for 6 hours
    ][run - 1]],
    'liquidity_demand_events': [lambda run, timestep, df=None: 0],
    'token_swap_events': [lambda run, timestep, df=None: 0],
}
params.update(params_override)

# Experiment details
now = datetime.datetime.now()
dir_path = os.path.dirname(os.path.realpath(__file__))
experiment_folder = __file__.split('.py')[0]
results_id = now.isoformat()

if __name__ == "__main__":
    run_experiment(results_id, experiment_folder, experiment_metrics, timesteps=SIMULATION_TIMESTEPS, runs=MONTE_CARLO_RUNS, params=params, initial_state=state_variables, save_file=True, save_logs=True)
