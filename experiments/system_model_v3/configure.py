import numpy as np
import itertools


timestep_duration = 0.004 # seconds

def generate_params(sweeps):
    cartesian_product = list(itertools.product(*sweeps.values()))
    params = {key: [x[i] for x in cartesian_product] for i, key in enumerate(sweeps.keys())}
    return params

def configure_experiment(sweeps: dict, timesteps=24*30*6, runs=1):
    params = generate_params(sweeps)
    param_sweeps = len(params[next(iter(params))])

    experiment_seconds = runs * param_sweeps * timesteps * timestep_duration
    experiment_metrics = f'''
    * Number of timesteps: {timesteps} / {timesteps / 24} days
    * Number of MC runs: {runs}
    * Timestep duration: {timestep_duration} seconds
    * Control parameters: {list(params.keys())}
    * Number of parameter combinations: {param_sweeps}
    * Expected experiment duration: {experiment_seconds / 60} minutes / {experiment_seconds / 60 / 60} hours
    '''
    print (experiment_metrics)

    return params, experiment_metrics
