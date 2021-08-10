# from .debt_market import eth_collateral
#from models.system_model_v3.model.parts.debt_market import open_cdp_lock
def open_cdp_lock(lock, eth_price, target_price, liquidation_ratio):
    # ETH * BASE/ETH / (BASE/RAI * unitless) -> RAI
    draw = lock * eth_price / (target_price * liquidation_ratio)
    return {
        "open": 1,
        "time": 0,
        "locked": lock,
        "drawn": draw,
        "wiped": 0.0,
        "freed": 0.0,
        "w_wiped": 0.0,
        "dripped": 0.0,
        "v_bitten": 0.0,
        "u_bitten": 0.0,
        "w_bitten": 0.0,
    }


from models.system_model_v3.model.state_variables.historical_state import eth_price
from models.system_model_v3.model.state_variables.system import target_price
import pandas as pd
import scipy

"""Settings for CDP agents."""
liquidation_ratio = 1.45
liquidation_buffer = 2
liquidity_cdp_count = 100 # Set to zero to disable liquidity CDPs

"""Initial balances for RAI/ETH Uniswap v2 pool."""
uniswap_rai_balance = 5e6
uniswap_eth_balance = uniswap_rai_balance * target_price / eth_price

"""Total capital given to all agents."""
total_starting_capital = 20e6 # Base

"""Capital share allocation for each agent."""
capital_allocation =  {'price_traders': 0/20, 'rate_traders': 5/20, 'eth_leverager': 20/20,
                       'malicious_whale': 0, 'arbitrage_cdp': 0, 'rai_lender': 0/20,
                       'rai_borrower': 0/20, 'base_rate_trader': 0/20, 'liquidity_cdps': 0/20,
                       'malicious_rai_trader': 0
                       }

def init(total_starting_capital, capital_allocation):
    """Initialize starting capital for all the agents."""
    #arbitrage_cdp_rai_balance =  capital_allocation["arbitrage_cdp"] * total_starting_capital / target_price
    #arbitrage_cdp_eth_collateral = arbitrage_cdp_rai_balance * liquidation_ratio * target_price / eth_price

    arbitrage_cdp_eth_collateral = capital_allocation["arbitrage_cdp"] * total_starting_capital / eth_price

    # Price and Rate Traders
    price_trader_rai_balance = capital_allocation["price_traders"] * total_starting_capital / target_price / 2
    price_trader_base_balance = price_trader_rai_balance * target_price

    rate_trader_rai_balance = capital_allocation["rate_traders"] * total_starting_capital / target_price / 2
    rate_trader_base_balance = rate_trader_rai_balance * target_price

    malicious_whale_rai_balance = capital_allocation["malicious_whale"] * total_starting_capital / target_price / 2
    malicious_whale_eth_balance = malicious_whale_rai_balance * target_price / eth_price

   
    liquidity_cdp_rai_balance = capital_allocation["liquidity_cdps"] * total_starting_capital / \
                                  (liquidation_ratio * liquidation_buffer) / target_price
    
    liquidity_cdp_eth_collateral = liquidity_cdp_rai_balance * (liquidation_ratio * liquidation_buffer) * \
                                   target_price / eth_price

    eth_leverager_rai_balance = capital_allocation["eth_leverager"] * total_starting_capital / \
                                  (liquidation_ratio * liquidation_buffer) / target_price
    
    eth_leverager_eth_balance = capital_allocation["eth_leverager"] * total_starting_capital / eth_price

    cap = capital_allocation["eth_leverager"] * total_starting_capital

    rai_lender_balance = capital_allocation["rai_lender"] * total_starting_capital / target_price 
    rai_borrower_balance = capital_allocation["rai_borrower"] * total_starting_capital / target_price 
    base_rate_trader_balance = capital_allocation["base_rate_trader"] * total_starting_capital / target_price

    malicious_rai_trader_balance = capital_allocation["malicious_rai_trader"] * total_starting_capital / target_price

    return arbitrage_cdp_eth_collateral, \
           price_trader_rai_balance, price_trader_base_balance, \
           rate_trader_rai_balance, rate_trader_base_balance, \
           malicious_whale_rai_balance, malicious_whale_eth_balance, \
           liquidity_cdp_rai_balance, liquidity_cdp_eth_collateral, \
           eth_leverager_rai_balance, eth_leverager_eth_balance, \
           rai_lender_balance, rai_borrower_balance, \
           base_rate_trader_balance, \
           malicious_rai_trader_balance

"""Variables that are used in the agents code to define how much capital each agent has."""
arbitrage_cdp_eth_collateral, \
price_trader_rai_balance, price_trader_base_balance, \
rate_trader_rai_balance, rate_trader_base_balance, \
malicious_whale_rai_balance, malicious_whale_eth_balance, \
liquidity_cdp_rai_balance, liquidity_cdp_eth_collateral, \
eth_leverager_rai_balance, eth_leverager_eth_balance, \
rai_lender_balance, rai_borrower_balance, \
base_rate_trader_balance, \
malicious_rai_trader_balance = init(total_starting_capital, capital_allocation)

cdp = {
    'open': 1, # Is the CDP open or closed? True/False == 1/0 for integer/float series
    'arbitrage': 0, # is this the arbitrage CDP
    'time': 0, # How long the CDP has been open for
    'locked': 0, # Collateral locked
    'drawn': 0, # Debt drawn
    'wiped': 0.0, # Principal debt wiped
    'freed': 0.0, # ETH collateral freed
    'w_wiped': 0.0, # Accrued interest wiped
    'v_bitten': 0.0, # ETH collateral bitten (liquidated)
    'u_bitten': 0.0, # Principal debt bitten
    'w_bitten': 0.0, # Accrued interest bitten
    'dripped': 0.0, # Total interest accrued
    'owner': '' #specifies which agent code controls the cdp
}

cdps = pd.DataFrame([cdp])
