import math
import numpy as np
import time
import logging
import pandas as pd
import statistics
from decimal import * 

from .utils import approx_greater_equal_zero, assert_log, approx_eq
from .debt_market import open_cdp_draw, open_cdp_lock, draw_to_liquidation_ratio, is_cdp_above_liquidation_ratio, wipe_to_liquidation_ratio, draw_to_liquidation_ratio
from .uniswap import get_output_price, get_input_price
import models.system_model_v3.model.parts.failure_modes as failure

"""
This file includes 3 money market trading agents:
RAI Lender: if lend_rate + RR > 0, buy RAI and loan it out, otherwise sell RAI
RAI Borrower: if RR < 0 and abs(RR) >= borrow rate, borrow RAI and sell, when not, repay and BUY
Base Rate Trader: if RR > external interest rate(Base), buy RAI, otherwise sell RAI for BASE

These strategies are not followed exactly as the plan is to simulate that there is multiple players in the field and also the bigger the profit opportunity there is, the more capital should be abusing the rate.
This is simulated with linear relationship between the possible profit and max apy diff ( a parameter):
Capital deployed = rate_difference/max_APY_diff c [-1,1]
when Capital deployed is 1, the agent sells all possible RAI it can, if its -1 it will sell all possible RAI. The max amount is defined by a parameter.
"""

def moneyMarketStateChange(params, state, our_state, share, max_rai_balance):
    """
    A helper function that sells or buy RAI depending on the share and max balance that the agent can be. All the 3 trading strategies use this to execute their strategy.
    if share = 1 => sell all RAI. 
    if share = -1 => buy all RAI
    """

    uniswap_state_delta = {
        'RAI_delta': 0,
        'ETH_delta': 0,
        'UNI_delta': 0,
    }

    RAI_balance = state['RAI_balance']
    ETH_balance = state['ETH_balance']
    uniswap_fee = params['uniswap_fee']
    
    trade_interest = float(share*max_rai_balance)
    trade_size = abs(trade_interest-our_state)
    
    #limit the trade at max to 5% of our balance so we dont just dump it at once
    if(trade_size > 0.05 * max_rai_balance):
        trade_size = 0.05 * max_rai_balance

    if(trade_interest > our_state):
        RAI_delta, ETH_delta = get_input_price(trade_size, RAI_balance, ETH_balance, uniswap_fee) # sell rai
        if ETH_delta <= 0 and RAI_delta >= 0 and ETH_balance + ETH_delta>0 and RAI_balance + RAI_delta>0:
            our_state += trade_size
            uniswap_state_delta['ETH_delta'] += ETH_delta
            uniswap_state_delta['RAI_delta'] += RAI_delta
    elif(trade_interest < our_state):
        RAI_delta, ETH_delta = get_input_price(-trade_size, RAI_balance, ETH_balance, uniswap_fee) #buy rai
    
        if ETH_delta >= 0 and RAI_delta <= 0 and ETH_balance + ETH_delta>0 and RAI_balance + RAI_delta>0:
            our_state -= trade_size
            uniswap_state_delta['ETH_delta'] += ETH_delta
            uniswap_state_delta['RAI_delta'] += RAI_delta

    return {**uniswap_state_delta, 'state': our_state}

def p_rai_lender(params, substep, state_history, state):
    """if lend_rate + RR > 0, buy RAI and loan it out, otherwise sell RAI (RAI Lender)"""
    APY = float(((1 + Decimal(state['target_rate'])) ** (60*60*24*365) - 1) * 100)

    share = -(state['compound_RAI_lend_APY'] + APY)/params['rai_lender_max_APY_diff']
    if share > 1:
        share = 1
    elif share < -1:
        share = -1
    
    if(state['compound_RAI_lend_APY'] + APY < 0):
        share = 1

    update = moneyMarketStateChange(params, state, state['rai_lender_state'], share, state['rai_lender_max_balance'])
    update['rai_lender_state'] = update['state']
    return {**update}

def s_store_rai_lender_state(params, substep, state_history, state, policy_input):
    return 'rai_lender_state', policy_input['rai_lender_state']

def p_rai_borrower(params, substep, state_history, state):
    """if RR < 0 and borrow rate > RR, borrow RAI and sell, when not, repay and BUY"""
    APY = float(((1 + Decimal(state['target_rate'])) ** (60*60*24*365) - 1) * 100)

    share = (state['compound_RAI_borrow_APY'] - APY)/params['rai_borrower_max_APY_diff']
    if share > 1:
        share = 1
    elif share < -1:
        share = -1

    if APY < 0:
        share = -1
        
    update = moneyMarketStateChange(params, state, state['rai_borrower_state'], share, state['rai_borrower_max_balance'])
    update['rai_borrower_state'] = update['state']
    return {**update}

def s_store_rai_borrower_state(params, substep, state_history, state, policy_input):
    return 'rai_borrower_state', policy_input['rai_borrower_state']

def p_base_rate_trader(params, substep, state_history, state):
    """if RR > external interest rate(BASE), buy RAI, otherwise sell RAI for BASE"""
    APY = float(((1 + Decimal(state['target_rate'])) ** (60*60*24*365) - 1) * 100)

    share = (state['external_BASE_APY'] - APY)/params['base_rate_trader_max_APY_diff']
    if share > 1:
        share = 1
    elif share < -1:
        share = -1

    #move all to external market if target rate is negative and external is positive
    if APY <= 0:
        if state['external_BASE_APY'] > 0:
            share = 1
    
    update = moneyMarketStateChange(params, state, state['base_rate_trader_state'], share, state['base_rate_trader_max_balance'])
    update['base_rate_trader_state'] = update['state']
    return {**update}

def s_store_base_rate_trader_state(params, substep, state_history, state, policy_input):
    return 'base_rate_trader_state', policy_input['base_rate_trader_state']

if __name__ == "__main__":
    import doctest
    doctest.testmod()
