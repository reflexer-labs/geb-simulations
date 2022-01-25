import math
import random
from decimal import *
import logging
import scipy

from .uniswap import get_output_price, get_input_price, buy_to_price, sell_to_price
import models.system_model_v3.model.parts.failure_modes as failure

def init_rate_traders(params, state):
    """
    Initialize all rate traders with their own entry deviation(mean and min percent) and
    their own timeframe(mean and min days) from independent normal distributions.
    Currently, all traders have equal balances
    See simulation blog post 2 for more info
    """
    assert params['rate_trader_mean_pct'] >= params['rate_trader_min_pct']

    # independently draw rate trader pct and days values from two normal distributions
    rate_trader_bounds = scipy.stats.norm.rvs(loc=params['rate_trader_mean_pct'],
                                              scale=params['rate_trader_std_pct'],
                                              size=params['rate_trader_count'])

    rate_trader_days = scipy.stats.norm.rvs(loc=params['rate_trader_mean_days'],
                                            scale=params['rate_trader_std_days'],
                                            size=params['rate_trader_count'])
    rate_trader_list = []
    for i in range(params['rate_trader_count']):
        rate_trader_list.append({
            'rai_balance': state['rate_trader_rai_balance']/params['rate_trader_count'],
            'base_balance': state['rate_trader_base_balance']/params['rate_trader_count'],
            'days': max(rate_trader_days[i], params['rate_trader_min_days']),
            'pct_bound': max(rate_trader_bounds[i], params['rate_trader_min_pct']),
            'n_buys': 0,
            'n_sells': 0
        })

    return rate_trader_list

def p_trade_rate(params, substep, state_history, state):
    """
    Trade RAI around redemption price.
    Sell when the market price is greater than (future_redemption_price * (1 + deviation) * premium).
    Buy when the market price is less than (future_redemption_price * (1 - deviation) * premium).
    Agent's behaviour is explained nicely in the simulations blog series.
    """
    uniswap_state_delta = {'RAI_delta': 0, 'ETH_delta': 0, 'UNI_delta': 0}
    debug = params['debug']
    timestep = state['timestep']

    if timestep == 1:
        if debug:
            print(f"Initializing rate traders. {state['rate_trader_rai_balance']}")
        rate_traders = init_rate_traders(params, state)
        return {'rate_traders': rate_traders, **uniswap_state_delta}


    RAI_balance = state['RAI_balance']
    ETH_balance = state['ETH_balance']
    UNI_supply = state['UNI_supply']

    eth_price = state['eth_price']
    uniswap_fee = params['uniswap_fee']

    updated_traders = []

    # process traders in random order
    for i, rate_trader in enumerate(random.sample(state['rate_traders'], len(state['rate_traders']))):
        effective_rate = 0
        try:
            effective_rate = float((1 + Decimal(state['target_rate'])) ** Decimal(60*60*24*rate_trader['days']))
        except (Overflow, FloatingPointError) as e:
            raise e
        
        # calculate future redemption price
        redemption_price = state['target_price'] * effective_rate * params['trader_market_premium']
        #if timestep > 7 * 24:
        #    print(f"{timestep=}, {i=}, {state['target_price']=:.6f}")
        #    print(f"{timestep=}, {i=}, {rate_trader['days']=}, {effective_rate=:.16f}, effective target price={redemption_price:.6f}")

        # get latest market price
        market_price = ETH_balance/RAI_balance * eth_price

        trader_rai_balance = rate_trader['rai_balance']
        trader_base_balance = rate_trader['base_balance']
        rate_trader_bound = rate_trader['pct_bound'] / 100

        updated_trader = {'rai_balance': trader_rai_balance,
                          'base_balance': trader_base_balance,
                          'days': rate_trader['days'],
                          'pct_bound': rate_trader['pct_bound'],
                          'n_buys': rate_trader['n_buys'],
                          'n_sells': rate_trader['n_sells']
                          }
        
        RAI_delta = 0
        ETH_delta = 0
        BASE_delta = 0
        UNI_delta = 0

        expensive_RAI = redemption_price * (1 + rate_trader_bound) < (1 - uniswap_fee) * market_price
        cheap_RAI = redemption_price * (1 - rate_trader_bound) > (1 + uniswap_fee) * market_price
        #i=14 pre rate-trader market price 3.149396 3.140000, 0.00, cheap_RAI=True, expensive_RAI=False
        #if timestep > 7 * 24:
        #    print(f"{timestep=}, {i=} pre rate-trader mp:{market_price:.6f}, rp:{redemption_price:.6f}, {rate_trader_bound:.4f}, {rate_trader['days']}, {cheap_RAI=}, {expensive_RAI=}")

        # How far to trade to the peg. 1 = all the way
        trade_ratio = random.uniform(0.8, 1.0)
        trade_ratio = 1.0
        if expensive_RAI and trader_rai_balance > 0:
            # sell rai to redemption price
            if params['debug']:
                print(f"{timestep=}, {ETH_balance=},{RAI_balance=}, {market_price=:.6f}, {redemption_price=:.6f}")

            # sell to redemption
            #desired_eth_rai = ETH_balance/RAI_balance * (redemption_price/market_price)
            try:
                #a = math.sqrt(RAI_balance * ETH_balance/desired_eth_rai) - RAI_balance
                a = sell_to_price(ETH_balance, RAI_balance, redemption_price, market_price)
            except ValueError as e:
                raise failure.PriceTraderConditionException(f'{RAI_balance=}, {ETH_balance=}, {desired_eth_rai=}')

            if a < 0:
                raise failure.PriceTraderConditionException(f'{a=}')

            # sell as much as we have or enough to move market to redemption price
            RAI_delta = min(trader_rai_balance, a * trade_ratio)

            if not RAI_delta > 0:
                RAI_delta = 0
                ETH_delta = 0
                BASE_delta = 0
            else:
                # Swap RAI for ETH
                _, ETH_delta = get_input_price(RAI_delta, RAI_balance, ETH_balance, uniswap_fee)
                if not ETH_delta < 0: raise failure.PriceTraderConditionException(f'{ETH_delta=}')
                if params['debug']:
                    print(f"{'rate trader selling':25} {RAI_delta=:.2f}, {ETH_delta=:.2f}, "
                          f"{market_price=:.6f}, {redemption_price=:.6f}")
                BASE_delta = ETH_delta * eth_price
                updated_trader['n_sells'] += 1

            updated_trader['rai_balance'] -= RAI_delta
            updated_trader['base_balance'] -= BASE_delta

            uniswap_state_delta['RAI_delta'] += RAI_delta
            uniswap_state_delta['ETH_delta'] += ETH_delta
            uniswap_state_delta['UNI_delta'] += UNI_delta

            # update pool locally after each trader
            RAI_balance += RAI_delta
            ETH_balance += ETH_delta
            #if state['timestep'] > 7 * 24:
            #    print(f"{i=} post rate-trader sell market price {(ETH_balance/RAI_balance * eth_price):.6f}")
           
        elif cheap_RAI and trader_base_balance > 0:
            # buy rai to redemption price
            if params['debug']:
                print(f"{timestep=}, {ETH_balance=}, {RAI_balance=}, {market_price=:.6f}, {redemption_price=:.6f}")
            desired_eth_rai = ETH_balance/RAI_balance * (redemption_price/market_price)

            try:
                a = math.sqrt(RAI_balance * ETH_balance/desired_eth_rai) - RAI_balance
                a = buy_to_price(ETH_balance, RAI_balance, redemption_price, market_price)
            except ValueError as e:
                raise failure.PriceTraderConditionException(f'{RAI_balance=}, {ETH_balance=}, {desired_eth_rai=}')

            if a < 0:
                raise failure.PriceTraderConditionException(f'{a=}')

            eth = trader_base_balance / eth_price
            _, rai_to_buy = get_input_price(eth, ETH_balance, RAI_balance, uniswap_fee)

            # buy as much as we can afford or enough to move market to redemption price
            RAI_delta = min(-rai_to_buy, a * trade_ratio)

            if not RAI_delta > 0:
                RAI_delta = 0
                ETH_delta = 0
                BASE_delta = 0
            else:
                ETH_delta, _ = get_output_price(RAI_delta, ETH_balance, RAI_balance, uniswap_fee)

                if not ETH_delta > 0: raise failure.PriceTraderConditionException(f'{ETH_delta=}')
                if params['debug']:
                    print(f"{'rate trader buying':25} {RAI_delta=:.2f}, {ETH_delta=:.2f}, "
                          f"{market_price=:.2f}, {redemption_price=:.2f}")
                BASE_delta = ETH_delta * eth_price
                updated_trader['n_buys'] += 1

            updated_trader['rai_balance'] += RAI_delta
            updated_trader['base_balance'] -= BASE_delta

            uniswap_state_delta['RAI_delta'] -= RAI_delta
            uniswap_state_delta['ETH_delta'] += ETH_delta
            uniswap_state_delta['UNI_delta'] += UNI_delta

            # update pool locally after each trader
            RAI_balance -= RAI_delta
            ETH_balance += ETH_delta
            #if state['timestep'] > 7 * 24:
            #    print(f"{i=} post rate-trader buy market price {(ETH_balance/RAI_balance * eth_price):.6f}")

        updated_traders.append(updated_trader)

    return {'rate_traders': updated_traders, **uniswap_state_delta}

def s_store_rate_traders(params, substep, state_history, state, policy_input):
    return 'rate_traders', policy_input['rate_traders']

if __name__ == "__main__":
    import doctest
    doctest.testmod()
