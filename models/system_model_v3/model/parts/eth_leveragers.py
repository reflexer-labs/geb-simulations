import pandas as pd
from .utils import target_rate_to_apy
from .debt_market import is_cdp_above_liquidation_ratio
from .debt_market import wipe_to_rr_apy, draw_to_rr_apy
from .uniswap import get_output_price, get_input_price

"""
A DEFI saver kind of an agent.
The agent keeps a CDP open and keeps its liquidation ratio between
"eth_leverager_target_min_liquidity_ratio" and "eth_leverager_target_max_liquidity_ratio". 
When the liquidation ratio goes out of these predefined ranges, the agent pushes the
liquidation to approximately to an average of these numbers
The purpose is to keep constant leverage on ETH.  This agent believes that ETH is going
up over time (relative to RAI).
"""
def p_leverage_eth(params, substep, state_history, state):
    debug = params['debug']

    uniswap_state_delta = {
        'RAI_delta': 0,
        'ETH_delta': 0,
        'UNI_delta': 0,
    }

    cdps = state['cdps'].copy()

    if state["timestep"] == 1:
        if debug:
            print("Initializing ETH Leverager")
        new_cdp = [{
            'open': 1, # Is the CDP open or closed? True/False == 1/0 for integer/float series
            'arbitrage': 0,
            'time': 0, # How long the CDP has been open for
            'locked': state['eth_leverager_eth_balance'],
            'drawn': state['eth_leverager_rai_balance'],
            'wiped': 0.0, # Principal debt wiped
            'freed': 0.0, # ETH collateral freed
            'w_wiped': 0.0, # Accrued interest wiped
            'v_bitten': 0.0, # ETH collateral bitten (liquidated)
            'u_bitten': 0.0, # Principal debt bitten
            'w_bitten': 0.0, # Accrued interest bitten
            'dripped': 0.0, # Total interest accrued
            'owner': 'leverager' #specifies which agent code controls the cdp
        }]

        new_cdp = pd.DataFrame(new_cdp)
        cdps = pd.concat((cdps, new_cdp), ignore_index=True)

        return {"cdps": cdps, **uniswap_state_delta}

    eth_price = state["eth_price"]
    target_price = state["target_price"]
    RAI_balance = state['RAI_balance']
    ETH_balance = state['ETH_balance']
    uniswap_fee = params['uniswap_fee']

    rr_apy = target_rate_to_apy(state['target_rate'])
    #operate only cdps that are managed by this agent
    for index, cdp_at_start in cdps.query("open == 1").query("owner == 'leverager'").iterrows():
        RAI_delta = 0
        ETH_delta = 0
        
        #perform actions on the SAFE only if we are above or below the threshold rates
        above_min = is_cdp_above_liquidation_ratio(cdps.loc[index], eth_price, target_price,
                params["eth_leverager_target_min_liquidity_ratio"])
        above_max = is_cdp_above_liquidation_ratio(cdps.loc[index], eth_price, target_price,
                params["eth_leverager_target_max_liquidity_ratio"])

        if not above_min or above_max:
            #calculate how we need to change the cdp to get the liquidation ratio to the preferred rate
            preferred_ratio = (params["eth_leverager_target_min_liquidity_ratio"] + \
                               params["eth_leverager_target_max_liquidity_ratio"])/2

            drawn_total = cdps.at[index, "drawn"] - cdps.at[index, "wiped"] - cdps.at[index, "u_bitten"] 
            locked_total = cdps.at[index, "locked"] - cdps.at[index, "freed"] - cdps.at[index, "v_bitten"]

            p_uniswap = RAI_balance / ETH_balance
            d_locked = (preferred_ratio * state['target_price'] * drawn_total - locked_total * state['eth_price']) \
                     / (state['eth_price'] - preferred_ratio * state['target_price'] * p_uniswap)
            d_drawn = p_uniswap * d_locked
           
            cdp_above_liquidation_buffer = is_cdp_above_liquidation_ratio(cdps.loc[index], eth_price,
                    target_price, preferred_ratio)
            if not cdp_above_liquidation_buffer and rr_apy > params['min_redemption_rate']:
                # too low liquidation ratio, pump it higher
                # unlock ETH, sell ETH for RAI, wipe debt

                RAI_delta, ETH_delta = get_output_price(d_locked, RAI_balance, ETH_balance, uniswap_fee)

                if params['min_redemption_rate'] <= -100 or params['kp'] == 0:
                    wiped = -RAI_delta
                    freed = ETH_delta
                else:
                    wipe_apy = wipe_to_rr_apy(params['min_redemption_rate'], ETH_balance, RAI_balance, eth_price, state, params)
                    wiped = min(-RAI_delta, wipe_apy)

                    RAI_delta, ETH_delta = get_input_price(-wiped, RAI_balance, ETH_balance, uniswap_fee)
                    freed = ETH_delta

                assert d_locked <= 0 # - ETH_delta

                # Make sure that no balance goes negative and then perform the swap if possible.
                # The swaps can go negative if uniswap lacks liquidity

                if freed <= locked_total and wiped <= drawn_total and wiped < RAI_balance:

                    cdps.at[index, "freed"] = cdps.at[index, "freed"] + freed
                    cdps.at[index, "wiped"] = cdps.at[index, "wiped"] + wiped

                    # update uniswap
                    uniswap_state_delta['ETH_delta'] += freed
                    uniswap_state_delta['RAI_delta'] -= wiped
                    ETH_balance += freed
                    RAI_balance -= wiped

            elif cdp_above_liquidation_buffer and rr_apy < params['max_redemption_rate']:
                # too high liquidation ratio, dump it lower
                # draw debt, sell RAI for ETH, lock ETH
                RAI_delta, ETH_delta = get_input_price(d_drawn, RAI_balance, ETH_balance, uniswap_fee)

                if params['max_redemption_rate'] == float("inf") or params['kp'] == 0:
                    drawn = RAI_delta
                    locked = -ETH_delta
                else:
                    draw_apy = draw_to_rr_apy(params['max_redemption_rate'], ETH_balance, RAI_balance, eth_price, state, params)
                    drawn = min(RAI_delta, draw_apy)

                    RAI_delta, ETH_delta = get_input_price(drawn, RAI_balance, ETH_balance, uniswap_fee)
                    locked = -ETH_delta

                assert d_locked >= 0

                # Make sure that no balance goes negative and then perform the swap if possible.
                # The swaps can go negative if uniswap lacks liquidity
                if locked <= ETH_balance:
                    cdps.at[index, "locked"] = cdps.at[index, "locked"] + locked
                    cdps.at[index, "drawn"] = cdps.at[index, "drawn"] + drawn

                    # update uniswap
                    uniswap_state_delta['ETH_delta'] -= locked
                    uniswap_state_delta['RAI_delta'] += drawn
                    ETH_balance -= locked
                    RAI_balance += drawn

    return {"cdps": cdps, **uniswap_state_delta}

if __name__ == "__main__":
    import doctest
    doctest.testmod()
