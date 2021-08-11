# GEB Controller Simulations

# Overview

[The Reflexer GEB System is a decentralized protocol that reacts to market forces in order to modify the value of a collateralized asset.](https://medium.com/reflexer-labs/stability-without-pegs-8c6a1cbc7fbd). The Reflexer GEB system allows anyone to leverage crypto assets to issue stablecoins, the first one of this kind being RAI. The goal of the system is to stabilize the secondary market price for Rai debt, using the redemption price as a stabilizer. The benefits of such stabilization is a reduction in both the volatility of the market price and its deviation from the redemption price. This increases predictability, while at the same time creating a flexible response instrument that can counteract or dampen unanticipated market shocks (such as liquidity cascades arising outside of the system).

To achieve this goal, Reflexer Labs implemented a Proportional-Integral-Derivative (PID) controller based upon a reference document approach for the [Maker DAI market](https://steemit.com/makerdao/@kennyrowe/digital-money-a-simulation-of-the-deflation-rate-adjustment-mechanism-of-the-dai-stablecoin) that was never implemented. The PID controller is the most commonly used controller type in the world, and both its modeling structure and its parameter tuning are well-researched problems.

## Goals

The goal of this repository is to create a [cadCAD](https://https://cadcad.org/) model to simulate the RAI system although the code can be adapted for any other GEB deployment. The simulations used here will help integrate a PID controller into the GEB system and select the parameters that optimize how the system responds to price changes. The overall objectives for the controller are:

* Smoothing out secondary market price movements
* Stability for the controller itself and for the redemption price in the case of a wode range of exogenous shocks

# The System

The simulations are done with a cadCAD system model of RAI components, using stochastic Ethereum prices and liquidity demand events such as exogenous processes, under different PI controller settings and a variety of agents acting within the RAI system.

cadCAD simulates systems in discrete time by maintaining state variables which are updated by state update functions.  These state updates are evaluated at each discrete time-step in Partial State Update Blocks (PSUBs).

If you are unfamiliar with the cadCAD architecture, it would be beneficial to visit [this page](https://github.com/cadCAD-org/cadCAD/blob/master/documentation/README.md).

If you just want to run a quick simulation, skip to the `QuickStart` section below.

## System Mechanisms

### Controller Specification

For a great, "plan English" overview of a PID controller, visit the Rai [whitepaper](https://github.com/reflexer-labs/whitepapers/blob/master/English/rai-english.pdf)

Here is the mathematical representation of the Rai Controller that sets the redemption rate:
![Controller](diagrams/controller.png)

### Partial State Update Blocks

PSUBs are where the state update functions are defined and change the RAI system state. State update functions within a PSUB run simultaneously, while PSUBs themselves are run in serial for each time-step in the simulation. They are defined in [partial_state_update_blocks.py](./models/system_model_v3/model/partial_state_update_blocks.py), where they can be enabled or disabled.

You can see all PSUBs of the current cadCAD model in the [PSUB diagram](./diagrams/BSCI_V3.png).

### Agents

Outside of the RAI core system, the simulation makes use of many agents, each implemented as a PSUB. You can see the agents listed in the PSUB diagram above and read more about their behavior in the [Agent Catalog](./agents.md)

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

From jupyter-lab, open and run `notebooks/experiments/system_model_v3/notebook-controller-run-analyze-grouped.ipynb`

# Repo Structure

Each model is located under `models/_`, with a unique name for each experiment.

* `models/run.py` - script to run simulation experiments from cli(can also run from notebooks)
* `models/system_model_v3/model` - model configuration (e.g. PSUBs, state variables)
* `models/system_model_v3/model/parts` - model logic, state update functions, and policy functions

Directories:

* `cross-model/` - simulate the Solidity controller alongside the cadCAD implemented controller
* `diagrams/` - system diagrams, used in documentation
* `experiments/` - experiment results, code, and run logs.
* `models/` - system and subsystem models, as well as ML/regression model development
* `notebooks/` - lab notebooks for model simulation and visualization using cadCAD (some notebooks have synced `.py` templates, see "Notebooks" below)

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

1. [RAI Mainnet subgraph access](notebooks/analysis/TheGraphDataSetCreation.ipynb)
2. [RAI Mainnet subgraph analysis](notebooks/analysis/TheGraphDataAnalysis.ipynb)

# Parameter selection methodology

* [System Parameter Methodology](parameter_methodology.md)

# Solidity / cadCAD "Cross Model"

Requires NodeJS/NPM (v10.13.0)

* Model code: `cross-model/`

## Run cadCAD Cross-Model Simulation

Notebook to validate that the controller implementation in cadCAD matches the implementation in prod/Solidity.

```bash
cd ./cross-model/truffle
npm install
npm run setup-network
jupyter-lab
# Open and run notebooks/solidity_cadcad/notebook_solidity_validation.ipynb
```
