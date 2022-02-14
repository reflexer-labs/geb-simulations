import scipy.stats as sts
import numpy as np
import copy
import random
import logging
import math

import models.system_model_v3.model.parts.uniswap as uniswap
from .utils import print_time


def p_liquidity_demand(params, substep, state_history, state):
    """Performs two kinds of liquidity operations on Uniswap based on DAI historical data:
    1) Make a random RAI/ETH swap on uniswap pool
    2) Put more stuff to RAI/ETH liquidity or take it out

    The data is percentage based calculated from the current pool size. This enables us to change the poolsize and its not tied to one fixed size.
    """
    if params['liquidity_demand_enabled']:
        RAI_balance = state['RAI_balance']
        ETH_balance = state['ETH_balance']
        UNI_supply = state['UNI_supply']

        market_price = state['market_price']
        eth_price = state['eth_price']
        
        uniswap_fee = params['uniswap_fee']

        swap = random.randint(0, 1)
        # Positive == swap in, or add liquidity event; negative == swap out or remove liquidity event
        direction = 1 if random.randint(0, 1) else -1

        UNI_delta = 0
        if swap:
            # Draw from swap process using as percentage amounts from the uniswap balance
            RAI_delta_pct = abs(params['token_swap_pct_events'](state['run'], state['timestep']))
            if params['liquidity_demand_shock']:
                RAI_delta = min(RAI_delta_pct * RAI_balance, 
                                RAI_balance * params['liquidity_demand_shock_percentage'])
            else:
                RAI_delta = min(RAI_delta_pct * RAI_balance,
                                RAI_balance * params['liquidity_demand_max_percentage'])

            RAI_delta = RAI_delta * direction

            if RAI_delta >= 0:
                # Selling RAI
                _, ETH_delta = uniswap.get_input_price(RAI_delta, RAI_balance, ETH_balance, uniswap_fee)
                assert ETH_delta <= 0, (ETH_delta, RAI_delta)
                assert ETH_delta <= ETH_balance, (ETH_delta, ETH_balance)
            else:
                # Buying RAI
                ETH_delta, _ = uniswap.get_output_price(abs(RAI_delta), ETH_balance, RAI_balance, uniswap_fee)
                assert ETH_delta > 0, (ETH_delta, RAI_delta)
                assert RAI_delta <= RAI_balance, (RAI_delta, RAI_balance)
        else:
            # Draw from liquidity process
            RAI_delta_pct = abs(params['liquidity_demand_pct_events'](state['run'], state['timestep']))

            if params['liquidity_demand_shock']:
                RAI_delta = min(RAI_delta_pct * RAI_balance, 
                                RAI_balance * params['liquidity_demand_shock_percentage'])
            else:
                RAI_delta = min(RAI_delta_pct * RAI_balance,
                                RAI_balance * params['liquidity_demand_max_percentage'])

            RAI_delta = RAI_delta * direction

            if RAI_delta >= 0:
                ETH_delta, RAI_delta, UNI_delta = uniswap.add_liquidity(ETH_balance, RAI_balance, UNI_supply, RAI_delta, RAI_delta * market_price / eth_price)
                assert ETH_delta >= 0
                assert RAI_delta >= 0
                assert UNI_delta >= 0
            else:
                ETH_delta, RAI_delta, UNI_delta = uniswap.remove_liquidity(ETH_balance, RAI_balance, UNI_supply, abs(RAI_delta))
                assert ETH_delta <= 0
                assert ETH_delta <= ETH_balance, (ETH_delta, ETH_balance)
                assert RAI_delta <= 0
                assert UNI_delta <= 0

        #print(f"Secondary market {state['timestep']}, {'swap' if swap else 'liquidity demand'}: {RAI_balance=},{RAI_delta=} {ETH_delta=} {UNI_delta=}")
        return {'RAI_delta': RAI_delta, 'ETH_delta': ETH_delta, 'UNI_delta': UNI_delta}
    else:
        return {'RAI_delta': 0, 'ETH_delta': 0, 'UNI_delta': 0}
    
def s_slippage(params, substep, state_history, state, policy_input):
    """Calculates slippage for current policy input"""
    swap = not policy_input['UNI_delta']
    if swap:
        expected_market_price = state['market_price']
        realized_market_price = ((state['ETH_balance'] + policy_input['ETH_delta']) / (state['RAI_balance'] + policy_input['RAI_delta'])) * state['eth_price']
        market_slippage = 1 - realized_market_price / expected_market_price
    else:
        market_slippage = math.nan
    return 'market_slippage', market_slippage

def s_liquidity_demand(params, substep, state_history, state, policy_input):
    liquidity_demand = policy_input['RAI_delta']
    return 'liquidity_demand', liquidity_demand

def s_liquidity_demand_mean(params, substep, state_history, state, policy_input):
    liquidity_demand = policy_input['RAI_delta']
    liquidity_demand_mean = (state['liquidity_demand_mean'] + liquidity_demand) / 2
    return 'liquidity_demand_mean', liquidity_demand_mean

'''

def p_market_price(params, substep, state_history, state):
    """Calculates market price of RAI based on the Uniswap balances """
    market_price = (state['ETH_balance'] / state['RAI_balance']) * state['eth_price']

    uniswap_oracle = copy.deepcopy(state['uniswap_oracle'])
    uniswap_oracle.update_result(state)
    median_price = uniswap_oracle.median_price

    return {"market_price": market_price, "market_price_twap": median_price, "uniswap_oracle": uniswap_oracle}

def s_market_price(params, substep, state_history, state, policy_input):
    return "market_price", policy_input["market_price"]

def s_market_price_twap(params, substep, state_history, state, policy_input):
    return "market_price_twap", policy_input["market_price_twap"]
'''

def s_uniswap_oracle(params, substep, state_history, state, policy_input):
    return "uniswap_oracle", policy_input["uniswap_oracle"]

# New
def p_spot_market_price(params, substep, state_history, state):
    """Calculates market price of RAI """
    spot_market_price = state['USD_balance'] / state['RAI_balance']
    return {"spot_market_price": spot_market_price}

def s_spot_market_price(params, substep, state_history, state, policy_input):
    return "spot_market_price", policy_input["spot_market_price"]

def p_market_price(params, substep, state_history, state):
    """Calculates Chainlink RAI/USD feed answer """

    # can be some median of market prices in the future
    current_answer = state['spot_market_price']

    # price movement
    if abs((current_answer - state['market_price']) / state['market_price']) >= params['chainlink_deviation_threshold']:
        answer = current_answer
        ts = state['cumulative_time']
    # stale
    elif state['cumulative_time'] - state['market_price_timestamp'] > params['chainlink_staleness_threshold']:
        answer = current_answer
        ts = state['cumulative_time']
    # use existing answer
    else:
        answer = state['market_price']
        ts = state['market_price_timestamp']

    return {"market_price": answer, "market_price_timestamp": ts}

def s_market_price(params, substep, state_history, state, policy_input):
    return "market_price", policy_input["market_price"]

def s_market_price_timestamp(params, substep, state_history, state, policy_input):
    return "market_price_timestamp", policy_input["market_price_timestamp"]

'''
def p_market_price_twap(params, substep, state_history, state):
    """Calculates Chainlink RAI/USD TWAP """
    twap_value = 3.50
    twap_obj = None

    return {"market_price_twap": twap_value, "market_price_twap_obj": twap_obj}
'''
def p_market_price_twap(params, substep, state_history, state):
    """Calculates Chainlink RAI/USD TWAP """

    market_price_twap_obj = copy.deepcopy(state['market_price_twap_obj'])
    market_price_twap_obj.update_result(state)
    twap_value = market_price_twap_obj.median_price

    return {"market_price_twap": twap_value, "market_price_twap_obj": market_price_twap_obj}

def s_market_price_twap(params, substep, state_history, state, policy_input):
    return "market_price_twap", policy_input["market_price_twap"]

def s_market_price_twap_obj(params, substep, state_history, state, policy_input):
    return "market_price_twap_obj", policy_input["market_price_twap_obj"]
