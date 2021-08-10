import math
import random
import logging

from .uniswap import get_output_price, get_input_price
import models.system_model_v3.model.parts.failure_modes as failure

def p_malicious_rai_trader_external_funding(params, substep, state_history, state):
    """
    Malicious Trader that trades against the controller. The agent is a simple P controller that moves funds agains the p controller by money god.
    """
    RAI_delta = 0
    ETH_delta = 0
    UNI_delta = 0
    
    RAI_balance = state['RAI_balance']
    ETH_balance = state['ETH_balance']
    uniswap_fee = params['uniswap_fee']
    eth_price = state["eth_price"]
    malicious_rai_trader_max_balance = params['malicious_rai_trader_max_balance'] #0.1
    
    state_change = {
        'malicious_rai_trader_state': state['malicious_rai_trader_state']
    }    
        
    uniswap_state_delta = {
        'RAI_delta': 0,
        'ETH_delta': 0,
        'UNI_delta': 0,
    }
    if(state['market_price_twap'] > 0):
        diff = (state['market_price_twap']-state['target_price'])/state['market_price_twap']*params['malicious_rai_trader_p']
        if(diff>1):
            diff = 1
        if(diff<-1):
            diff = -1
        trade_interest = diff*malicious_rai_trader_max_balance

        #print('trade_interest:' + str(trade_interest) + ' malicious_rai_trader_state:' + str(state_change['malicious_rai_trader_state']))
        if(trade_interest > state_change['malicious_rai_trader_state']):
            trade_size = trade_interest-state_change['malicious_rai_trader_state']
            # Exchange RAI for ETH, by short_size if we have enough eth for that
            RAI_delta, ETH_delta = get_input_price(trade_size, RAI_balance, ETH_balance, uniswap_fee)
            if ETH_delta <= 0 and RAI_delta >= 0 and ETH_balance + ETH_delta>0 and RAI_balance + RAI_delta>0:
                #print('RAI-ETH: RAI_delta: ' + str(RAI_delta) + ', ETH_delta:' + str(ETH_delta))
                state_change['malicious_rai_trader_state'] += trade_size
                uniswap_state_delta['ETH_delta'] += ETH_delta
                uniswap_state_delta['RAI_delta'] += RAI_delta
                ETH_balance += ETH_delta
                RAI_balance += RAI_delta
        elif(trade_interest < state_change['malicious_rai_trader_state']):
            trade_size = state_change['malicious_rai_trader_state'] - trade_interest
            # Exchange ETH for RAI
            RAI_delta, ETH_delta = get_input_price(-trade_size, RAI_balance, ETH_balance, uniswap_fee)
        
            if ETH_delta >= 0 and RAI_delta <= 0 and ETH_balance + ETH_delta>0 and RAI_balance + RAI_delta>0:
                #print('ETH-RAI: RAI_delta: ' + str(RAI_delta) + ', ETH_delta:' + str(ETH_delta))
                state_change['malicious_rai_trader_state'] -= trade_size
                uniswap_state_delta['ETH_delta'] += ETH_delta
                uniswap_state_delta['RAI_delta'] += RAI_delta
                ETH_balance += ETH_delta
                RAI_balance += RAI_delta

    return {**uniswap_state_delta, **state_change}

def s_store_malicious_rai_trader_state(params, substep, state_history, state, policy_input):
    return 'malicious_rai_trader_state', policy_input['malicious_rai_trader_state']

def p_constant_price_agent(params, substep, state_history, state):
    """
    A malicious agent that
    1) Pumps the price significantly at "malicious_whale_t1"
    2) tries to maintain the price at "malicious_whale_pump_percent*malicious_whale_p0"
    3) stops manipulation at "malicious_whale_t2"
    """
    
    RAI_balance = state['RAI_balance']
    ETH_balance = state['ETH_balance']
    UNI_supply = state['UNI_supply']
    uniswap_fee = params['uniswap_fee']

    uniswap_state_delta = {
        'RAI_delta': 0,
        'ETH_delta': 0,
        'UNI_delta': 0,
    }

    stateUpdate = {
        'malicious_whale_funds_eth': state['malicious_whale_funds_eth'],
        'malicious_whale_funds_rai': state['malicious_whale_funds_rai'],
        'malicious_whale_state': state['malicious_whale_state'],
        'malicious_whale_p0': state['malicious_whale_p0'],
    }

    RAI_balance = state['RAI_balance']

    ETH_delta = 0
    RAI_delta = 0
    funds_to_use_RAI = 0
    funds_to_use_ETH = 0
    if state['cumulative_time'] > params['malicious_whale_t1'] and state['cumulative_time'] < params['malicious_whale_t2']:
        if state['malicious_whale_state'] == 0:
            #Start the pump by initially pumping the price with 20% of funds. Also set the price we are pumping the RAI from
            stateUpdate['malicious_whale_p0'] = state['market_price_twap']
            wanted_price = stateUpdate['malicious_whale_p0'] * params['malicious_whale_pump_percent']
            fraction_to_use = 0.2
        else:
            #Use a p-controller to maintaing the price at malicious_whale_p0*malicious_whale_pump_percent
            stateUpdate['malicious_whale_p0'] = state['malicious_whale_p0']
            wanted_price = stateUpdate['malicious_whale_p0'] * params['malicious_whale_pump_percent']
            diff = abs((wanted_price - state['market_price_twap'])/state['market_price_twap']/abs(1-params['malicious_whale_pump_percent']) * params['malicious_whale_kp']) #a P-controller maintaining the price at wanted range
            if diff > 2:
                diff = 2
            #use at maxium 2 times the capital allocated for this timeslot, depending on the price difference
            #capital allocated for each timestemp is all the whales capital divided by the timespan the whale is active
            fraction_to_use = state['timedelta']/(params['malicious_whale_t2']-params['malicious_whale_t1'])*diff
            if fraction_to_use < 0:
                fraction_to_use = 0
        #print('fraction_to_use: ' + str(fraction_to_use))
        stateUpdate['malicious_whale_state'] = 1

        #maintain the market price at "wanted_price"
        if state['market_price_twap'] < wanted_price:
            funds_to_use_ETH = state['malicious_whale_funds_eth'] * fraction_to_use
            RAI_delta, ETH_delta = get_output_price(-funds_to_use_ETH, RAI_balance, ETH_balance, uniswap_fee)

        if state['market_price_twap'] > wanted_price:
            funds_to_use_RAI = state['malicious_whale_funds_rai'] * fraction_to_use
            RAI_delta, ETH_delta = get_input_price(funds_to_use_RAI, RAI_balance, ETH_balance, uniswap_fee)

        #only execute the swap if we can afford to do so
        if (stateUpdate['malicious_whale_funds_eth'] > ETH_delta and stateUpdate['malicious_whale_funds_rai'] > RAI_delta):
            uniswap_state_delta['ETH_delta'] += ETH_delta
            uniswap_state_delta['RAI_delta'] += RAI_delta
            ETH_balance += ETH_delta
            RAI_balance += RAI_delta
            stateUpdate['malicious_whale_funds_eth'] -= ETH_delta
            stateUpdate['malicious_whale_funds_rai'] -= RAI_delta
            #print(str(state['malicious_whale_state']) + "marketprice:" + str(state['market_price_twap'] )+ "(wanted: " + str(wanted_price) + ") RAI_delta" + str(RAI_delta) + ": ETH_delta" + str(ETH_delta) + " RAI Left: " + str(stateUpdate['malicious_whale_funds_rai']) + " ETH Left: " + str(stateUpdate['malicious_whale_funds_eth'])  )

    return {**stateUpdate, **uniswap_state_delta}

def s_store_malicious_whale_funds_eth(params, substep, state_history, state, policy_input):
    return 'malicious_whale_funds_eth', policy_input['malicious_whale_funds_eth']

def s_store_malicious_whale_funds_rai(params, substep, state_history, state, policy_input):
    return 'malicious_whale_funds_rai', policy_input['malicious_whale_funds_rai']

def s_store_malicious_whale_state(params, substep, state_history, state, policy_input):
    return 'malicious_whale_state', policy_input['malicious_whale_state']

def s_store_malicious_whale_p0(params, substep, state_history, state, policy_input):
    return 'malicious_whale_p0', policy_input['malicious_whale_p0']