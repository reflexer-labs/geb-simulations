import pandas as pd
import numpy as np
"""Retrieve presimulated chain actions such as eth price, token swapping, liquidity demand and such."""

#eth_price_df = pd.read_csv('models/system_model_v3/data/eth_values_gold.csv.gz', 
#eth_price_df = pd.read_csv('models/system_model_v3/data/ohm_values_mc.csv.gz', 
#eth_price_df = pd.read_csv('models/system_model_v3/data/eth_values_mc.csv.gz', 
#eth_price_df = pd.read_csv('models/system_model_v3/data/ohm_values_mc.csv.gz', 
eth_price_df = pd.read_csv('models/system_model_v3/data/eth_values_mc.csv.gz', 
                           compression='gzip',
                           index_col=0)

# Set the initial ETH price state
eth_price = eth_price_df["0"].iloc[0]

#Liquidity adds and removes to uniswap ETH/RAI pool
liquidity_demand_pct_df = pd.read_csv('models/system_model_v3/data/liquidity_pct_mc.csv.gz',
                                      compression='gzip',
                                      index_col=0)

#token trades in and out of the uniswap ETH/RAi pool
token_swap_pct_df = pd.read_csv('models/system_model_v3/data/buy_sell_pct_mc.csv.gz',
                                compression='gzip',
                                index_col=0)
