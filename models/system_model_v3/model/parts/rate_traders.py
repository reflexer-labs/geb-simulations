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
    uniswap_state_delta = {'RAI_delta': 0, 'USD_delta': 0, 'UNI_delta': 0}
    debug = params['debug']
    timestep = state['timestep']

    if timestep == 1:
        if debug:
            print(f"Initializing rate traders. {state['rate_trader_rai_balance']}")
        rate_traders = init_rate_traders(params, state)
        return {'rate_traders': rate_traders, **uniswap_state_delta}


    RAI_balance = state['RAI_balance']
    USD_balance = state['USD_balance']
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

        # get latest market price
        market_price = USD_balance/RAI_balance

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
        USD_delta = 0
        BASE_delta = 0
        UNI_delta = 0

        expensive_RAI = redemption_price * (1 + rate_trader_bound) < (1 - uniswap_fee) * market_price
        cheap_RAI = redemption_price * (1 - rate_trader_bound) > (1 + uniswap_fee) * market_price

        # How far to trade to the effective redemption price. 1 = all the way
        trade_ratio = random.uniform(0.1, 0.5)
        #trade_ratio = 1.0
        if expensive_RAI and trader_rai_balance > 0:
            # sell rai to redemption price
            if debug:
                print(f"{timestep=}, {USD_balance=},{RAI_balance=}, {market_price=:.6f}, {redemption_price=:.6f}")

            # sell to redemption
            try:
                rai_to_sell = sell_to_price(USD_balance, RAI_balance, redemption_price, market_price)
            except ValueError as e:
                raise failure.PriceTraderConditionException(f'{RAI_balance=}, {USD_balance=}, {desired_eth_rai=}')

            if rai_to_sell < 0: raise failure.PriceTraderConditionException(f'{rai_to_sell=}')

            # sell as much as we have or enough to move market to redemption price
            RAI_delta = min(trader_rai_balance, rai_to_sell * trade_ratio)

            if RAI_delta <= 0:
                RAI_delta = 0
                USD_delta = 0
                BASE_delta = 0
            else:
                # Swap RAI for USD
                _, USD_delta = get_input_price(RAI_delta, RAI_balance, USD_balance, uniswap_fee)
                if not USD_delta < 0: raise failure.PriceTraderConditionException(f'{USD_delta=}')
                if debug:
                    print(f"{'rate trader selling':25} {RAI_delta=:.2f}, {USD_delta=:.2f}, "
                          f"{market_price=:.6f}, {redemption_price=:.6f}")
                BASE_delta = USD_delta
                updated_trader['n_sells'] += 1

            updated_trader['rai_balance'] -= RAI_delta
            updated_trader['base_balance'] -= BASE_delta

            uniswap_state_delta['RAI_delta'] += RAI_delta
            uniswap_state_delta['USD_delta'] += USD_delta
            uniswap_state_delta['UNI_delta'] += UNI_delta

            # update pool locally after each trader
            RAI_balance += RAI_delta
            USD_balance += USD_delta
            #print(f"after trade market_price: {USD_balance/RAI_balance:.6f}")
           
        elif cheap_RAI and trader_base_balance > 0:
            # buy rai to redemption price
            if debug:
                print(f"{timestep=}, {USD_balance=}, {RAI_balance=}, {market_price=:.6f}, {redemption_price=:.6f}")

            try:
                rai_to_buy = buy_to_price(USD_balance, RAI_balance, redemption_price, market_price)
            except ValueError as e:
                raise failure.PriceTraderConditionException(f'{RAI_balance=}, {USD_balance=}, {desired_eth_rai=}')

            if rai_to_buy < 0: raise failure.PriceTraderConditionException(f'{rai_to_buy=}')

            #eth = trader_base_balance / eth_price
            #How much rai can be bought if using entire trader balance
            _, rai_delta_all = get_input_price(trader_base_balance, USD_balance, RAI_balance, uniswap_fee)
            if debug:
                print(f"{rai_to_buy=}, {rai_delta_all=}")

            # buy as much as we can afford or enough to move market to redemption price
            # RAI_delta will be positive when buying here
            RAI_delta = min(-rai_delta_all, rai_to_buy * trade_ratio)
            #print(f"{RAI_delta=}")

            if RAI_delta <= 0:
                RAI_delta = 0
                USD_delta = 0
                BASE_delta = 0
            else:
                USD_delta, _ = get_output_price(RAI_delta, USD_balance, RAI_balance, uniswap_fee)

                if not USD_delta > 0: raise failure.PriceTraderConditionException(f'{USD_delta=},{RAI_delta=}')
                if params['debug']:
                    print(f"{'rate trader buying':25} {RAI_delta=:.2f}, {USD_delta=:.2f}, "
                          f"{market_price=:.2f}, {redemption_price=:.2f}")
                BASE_delta = USD_delta
                updated_trader['n_buys'] += 1

            updated_trader['rai_balance'] += RAI_delta
            updated_trader['base_balance'] -= BASE_delta

            uniswap_state_delta['RAI_delta'] -= RAI_delta
            uniswap_state_delta['USD_delta'] += USD_delta
            uniswap_state_delta['UNI_delta'] += UNI_delta

            # update pool locally after each trader
            RAI_balance -= RAI_delta
            USD_balance += USD_delta
            #print(f"after trade market_price: {USD_balance/RAI_balance:.6f}")

        updated_traders.append(updated_trader)

    return {'rate_traders': updated_traders, **uniswap_state_delta}

def s_store_rate_traders(params, substep, state_history, state, policy_input):
    return 'rate_traders', policy_input['rate_traders']

if __name__ == "__main__":
    import doctest
    doctest.testmod()
