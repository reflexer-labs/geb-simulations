from experiments.utils import save_to_HDF5, update_experiment_run_log

from radcad import Model, Simulation, Experiment
from radcad.engine import Engine, Backend

from models.system_model_v3.model.partial_state_update_blocks import partial_state_update_blocks
from models.system_model_v3.model.params.init import params
from models.system_model_v3.model.state_variables.init import state_variables

from models.system_model_v3.model.params.init import eth_price_df

import logging
import datetime
import subprocess
import time
import os
import dill
import pandas as pd
import pprint


# Set according to environment
os.environ['NUMEXPR_MAX_THREADS'] = '8'

# Get experiment details
hash = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"]).strip().decode("utf-8")
now = datetime.datetime.now()

# Set the number of simulation timesteps, with a maximum of `len(debt_market_df) - 1`
#SIMULATION_TIMESTEPS = 24 * 30 * 6  # len(eth_price_df) - 1
#MONTE_CARLO_RUNS = 1


def configure_logging(output_directory, date):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    file_handler = logging.FileHandler(filename=f'{output_directory}/{date}.log')
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

def run_experiment(results_id=None, output_directory=None, experiment_metrics=None, timesteps=24*30*12,
                   runs=1, params=params, initial_state=state_variables,
                   state_update_blocks=partial_state_update_blocks,
                   save_file=False, save_logs=False):

    if save_logs:
        configure_logging(output_directory + '/logs', now)
    
    passed = False
    experiment_time = 0.0
    exceptions = []
    try:
        start = time.time()
        
        # Run experiment
        logging.info("Starting experiment")
        logging.debug(experiment_metrics)
        logging.info(pprint.pformat(params))

        # Run cadCAD simulation
        model = Model(
            initial_state=state_variables,
            state_update_blocks=partial_state_update_blocks,
            params=params
        )
        simulation = Simulation(model=model, timesteps=timesteps, runs=runs)
        experiment = Experiment([simulation])
        experiment.engine = Engine(
            backend=Backend.PATHOS,
            raise_exceptions=False,
            deepcopy=False,
            processes=8,
            drop_substeps=True,
        )
        if save_file:
            experiment.after_experiment = lambda experiment: save_to_HDF5(experiment,
                    output_directory + '/experiment_results.hdf5', results_id, now)
        experiment.run()
        
        exceptions = pd.DataFrame(experiment.exceptions)
        
        logging.debug(exceptions)
        #print(exceptions)

        passed = True
        end = time.time()
        experiment_time = end - start
        logging.info(f"Experiment completed in {experiment_time} seconds")

        #update_experiment_run_log(output_directory, passed, results_id, hash, exceptions, experiment_metrics, experiment_time, now)
        return pd.DataFrame(experiment.results)
    except AssertionError as e:
        pass
        #logging.info("Experiment failed")
        #logging.error(e)

        #update_experiment_run_log(output_directory, passed, results_id, hash, exceptions, experiment_metrics, experiment_time, now)
