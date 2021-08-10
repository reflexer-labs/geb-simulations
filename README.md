# Reflexer, GEB-Simulations


# Overview
[The Reflexer GEB System is a decentralized protocol that reacts to market forces to modify the value of a collateralized asset.](https://medium.com/reflexer-labs/stability-without-pegs-8c6a1cbc7fbd)  The Reflexer GEB system allows anyone to leverage crypto assets to issue a "reflex bond"(the only reflex bond currently deployed is Rai). The goal of the system is to stabilize the secondary market price for Rai debt, using the redemption price as a stabilizer. The benefits of such stabilization is a reduction in both the volatility of the market price and its deviation from the redemption price. This increases predictability, while at the same time creating a flexible response instrument that can counteract or dampen unanticipated market shocks (such as liquidity cascades arising outside of the system).

To achieve this goal, Reflexer Labs implemented a Proportional-Integral-Derivative (PID) controller based upon a reference document approach for the [Maker DAI market that was never implemented](https://steemit.com/makerdao/@kennyrowe/digital-money-a-simulation-of-the-deflation-rate-adjustment-mechanism-of-the-dai-stablecoin). The PID controller is the most commonly implemented real-world stability controller type in the world, and both its modeling structure and its parameter tuning are well-researched problems.

## Goals
The goal of this repository is to create a [cadCAD](https://https://cadcad.org/) model to simulate the Rai system. The simulations used here will help design the incorporation of a PID controller into the system, and select the parameters that optimize how the system responds to price changes in order to achieve overall objectives. In short, 
* Smoothing of secondary market price movements
* Stability of the controller, and thus the redemption price, for a range of exogenous shocks

# The System

The simulations are done with a cadCAD system model of RAI components, using stochastic Ethereum prices and liquidity demand events as exogenous proceses, under different PI controller settings and a variety of agents acting within the RAI system.

cadCad simulates systems in discrete time by maintaining state variables, which are updated by state update functions.  These updates of the states are evaluated at each discrete timestep in Partial State Update Blocks(PSUBs).

If you are unfamiliar with cadCAD architecture, it would be beneficial to visit [here](https://github.com/cadCAD-org/cadCAD/blob/master/documentation/README.md).

If you just want to run a simulation skip to the `QuickStart` section below.


## System Mechanisms
### Controller Specification
For a great, "plan English" overview of a PID controller, visit the Rai [whitepaper](https://github.com/reflexer-labs/whitepapers/blob/master/English/rai-english.pdf)

Here is the mathematical representation of the Rai Controller that sets the redemption rate:
![Controller](diagrams/controller.png)

### Partial State Update Blocks

PSUBs are where the state update functions are defined which change the Rai systemm state. State update functions within a PSUB are run simultaneously, while PSUBs themselves are run in serial for each timestep in the simulation. They are defined in [partial_state_update_blocks.py](./models/system_model_v3/model/partial_state_update_blocks.py), where they can be enabled or disabled.)

You can see all PSUBs of the current cadCAD model in the [PSUB diagram](./diagrams/BSCI_V3.png).

### Agents

Outside of the RAI core system, the simulation makes use of many agents, each implemented as a PSUB.  You can see the agents listed in the PSUB diagram above and read more about their behavior in the  [Agent Catalog](./agents.md) 

### System Glossary

* [System Glossary](./GLOSSARY.md)


# QuickStart

## Installation
Python 3.8

```
python -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install wheel
python -m pip install -r requirements.txt
python -m ipykernel install --user --name python-reflexer --display-name "Python (Reflexer)"
```

## Run a simulation

### Start Jupyter Lab

```bash
source venv/bin/activate
jupyter-lab
```

`jupyter-lab`

From Jupyter-Lab console, run `notebooks/experiments/system_model_v3/notebook-controller-run-analyze-grouped.ipynb`


# Repo Structure

Each model is located under `models/_`, with a unique name for each experiment.

* `models/run.py` - script to run simulation experiments
* `models/_/model` - model configuration (e.g. PSUBs, state variables)
* `models/_/model/parts` - model logic, state update functions, and policy functions

Directories:

* `diagrams/` - system diagrams, used in documentation
* `experiments/` - experiment results, code, and run logs.
* `exports/` - exports from simulations, such as datasets, charts, etc.
* `lib/` - third party libraries modified for use within models and simulations, such as Scipy which had to be patched
* `logs/` - output directory for cadCAD model logs (local only, in `.gitignore`)
* `models/` - system and subsystem models, as well as ML/regression model development
* `notebooks/` - lab notebooks for model simulation and visualization using cadCAD (some notebooks have synced `.py` templates, see "Notebooks" below)
* `plots/` - static plots used in notebooks
* `simulations/` - execution of simulation notebooks using Papermill
* `tests/` - `pytest` tests and misc. testing resources
* `utils/` - utility code used within notebooks, for example generating plots

Files:

* `shared.py` - file containing shared notebook imports and setup

# Notebooks

### Analysis and Simulations
Notebooks analysing the system and showcasing how to perform experiments and analysis.
1. [System Model Simple Run](notebooks/experiments/system_model_v3/notebook-controller-run-analyze-grouped.ipynb)
2. [System Model Simple Run, Faceted Visualization](notebooks/experiments/system_model_v3/notebook-controller-run-analyze-faceted.ipynb)
3. [Shock Tests](notebooks/experiments/system_model_v3/notebook-controller-shocks.ipynb)

### Stochastic Data Generation
1. [Eth Exogenous Process](notebooks/Stochastic_Generators/Eth_Exogenous_Process_Modeling.ipynb)
2. [Uniswap Exogenous Process](notebooks/Stochastic_Generators/Uniswap_Process_Modeling.ipynb)

### The Graph Data
8. [RAI Mainnet subgraph access](notebooks/analysis/TheGraphDataSetCreation.ipynb)
9. [RAI Mainnet subgraph analysis](notebooks/analysis/TheGraphDataAnalysis.ipynb)

# Parameter selection methodology

* [System Parameter Methodology](parameter_methodology.md)


# Solidity / cadCAD "Cross Model"

* Model code: `cross-model/`
*
## Run cadCAD Cross-Model Simulation

```bash
cd ./cross-model/truffle
npm install
npm run setup-network
# Open and run notebooks/solidity_cadcad/notebook_solidity_validation.ipynb
```


# Unit Tests

`python -m pytest ./tests`
