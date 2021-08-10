import math
import random
import logging
import scipy

from .uniswap import get_output_price, get_input_price
import models.system_model_v3.model.parts.failure_modes as failure

def init_price_traders(params, state):
    """
    Initialize all the price traders with their own rai and base balances
    from normal distribution (see simulation blog post 2 for more info)
    """
    assert params['price_trader_mean_pct'] > params['price_trader_min_pct']
    assert params['price_trader_count'] > 10

    price_trader_bounds = scipy.stats.norm.rvs(loc = params['price_trader_mean_pct'],
                                              scale = params['price_trader_std_pct'],
                                              size = params['price_trader_count'])
    price_trader_list = []
    for i in range(params['price_trader_count']):
        price_trader_list.append({
            'rai_balance': state['price_trader_rai_balance'] / params['price_trader_count'],
            'base_balance': state['price_trader_base_balance'] / params['price_trader_count'],
            'pct_bound': max(price_trader_bounds[i], params['price_trader_min_pct'])
        })

    return price_trader_list

def p_trade_price(params, substep, state_history, state):
    """
    Trade RAI around redemption price. 
    When market price goes above the market premium, sell.
    When market price goes below the market premium, buy.
    Agent behaviour is explained nicely here: https://hackmd.io/BcT6VQKESKGxSa1OxLKL_Q

    """
    
    uniswap_state_delta = {'RAI_delta': 0, 'ETH_delta': 0, 'UNI_delta': 0}
    debug = params['debug']

    if state['timestep'] == 1:
        if debug:
            print(f"Initializing price traders. {state['price_trader_rai_balance']}")
        price_traders = init_price_traders(params, state)
        return {'price_traders': price_traders, **uniswap_state_delta}

    RAI_balance = state['RAI_balance']
    ETH_balance = state['ETH_balance']
    UNI_supply = state['UNI_supply']

    redemption_price = state['target_price'] * params['trader_market_premium']
    eth_price = state['eth_price']
    market_price = ETH_balance/RAI_balance * eth_price
    uniswap_fee = params['uniswap_fee']

    updated_traders = []

    # process traders in random order
    for price_trader in random.sample(state['price_traders'], len(state['price_traders'])):
        trader_rai_balance = price_trader['rai_balance']
        trader_base_balance = price_trader['base_balance']
        price_trader_bound = price_trader['pct_bound'] / 100

        updated_trader = {'rai_balance': trader_rai_balance,
                          'base_balance': trader_base_balance,
                          'pct_bound': price_trader['pct_bound']}
        
        RAI_delta = 0
        ETH_delta = 0
        BASE_delta = 0
        UNI_delta = 0

        expensive_RAI_on_secondary_market = \
            redemption_price * (1 + price_trader_bound) < (1 - uniswap_fee) * market_price
        cheap_RAI_on_secondary_market = \
            redemption_price * (1 - price_trader_bound) > (1 - uniswap_fee) * market_price

        # How far to trade to the peg. 1 = all the way
        trade_ratio = 1/1
        if expensive_RAI_on_secondary_market and trader_rai_balance > 0:

            # sell to redemption
            desired_eth_rai = ETH_balance/RAI_balance * (redemption_price/market_price)
            a = math.sqrt(RAI_balance * ETH_balance/desired_eth_rai) - RAI_balance

            if a <= 0: raise failure.PriceTraderConditionException(f'{a=}')
            RAI_delta = min(trader_rai_balance, a * trade_ratio)

            if not RAI_delta >= 0:
                ETH_delta = 0
                BASE_delta = 0
            else:
                # Swap RAI for ETH
                _, ETH_delta = get_input_price(RAI_delta, RAI_balance, ETH_balance, uniswap_fee)
                if not ETH_delta < 0: raise failure.PriceTraderConditionException(f'{ETH_delta=}')
                if params['debug']:
                    print(f"{'price trader selling':25} {RAI_delta=:.2f}, {ETH_delta=:.2f}, "
                          f"{market_price=:.2f}, {redemption_price=:.2f}")
                BASE_delta = ETH_delta * eth_price

            updated_trader['rai_balance'] += -RAI_delta
            updated_trader['base_balance'] += -BASE_delta

            uniswap_state_delta['RAI_delta'] += RAI_delta
            uniswap_state_delta['ETH_delta'] += ETH_delta
            uniswap_state_delta['UNI_delta'] += UNI_delta

            # update pool locally after each trader
            RAI_balance += RAI_delta
            ETH_balance += ETH_delta
            market_price = ETH_balance/RAI_balance * eth_price
           
        elif cheap_RAI_on_secondary_market and trader_base_balance > 0:
            desired_eth_rai = ETH_balance/RAI_balance * (redemption_price/market_price)
            a = math.sqrt(RAI_balance * ETH_balance/desired_eth_rai) - RAI_balance

            if a >= 0: raise failure.PriceTraderConditionException(f'{a=}')

            RAI_delta = min(int(trader_base_balance / market_price), -a * trade_ratio)

            if not RAI_delta > 0:
                ETH_delta = 0
                BASE_delta = 0
            else:
                ETH_delta, _ = get_output_price(RAI_delta, ETH_balance, RAI_balance, uniswap_fee)
                if not ETH_delta > 0: raise failure.PriceTraderConditionException(f'{ETH_delta=}')
                if params['debug']:
                    print(f"{'price trader buying':25} {RAI_delta=:.2f}, {ETH_delta=:.2f}, "
                          f"{market_price=:.2f}, {redemption_price=:.2f}")
                BASE_delta = ETH_delta * eth_price

            updated_trader['rai_balance'] += RAI_delta
            updated_trader['base_balance'] += -BASE_delta

            uniswap_state_delta['RAI_delta'] += -RAI_delta
            uniswap_state_delta['ETH_delta'] += ETH_delta
            uniswap_state_delta['UNI_delta'] += UNI_delta

            # update pool locally after each trader
            RAI_balance += -RAI_delta
            ETH_balance += ETH_delta
            market_price = ETH_balance/RAI_balance * eth_price

        updated_traders.append(updated_trader)

    return {'price_traders': updated_traders, **uniswap_state_delta}

def s_store_price_traders(params, substep, state_history, state, policy_input):
    return 'price_traders', policy_input['price_traders']

if __name__ == "__main__":
    import doctest
    doctest.testmod()
