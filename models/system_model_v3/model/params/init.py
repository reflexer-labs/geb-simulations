import numpy as np
import pandas as pd

import models.options as options
from models.constants import SPY, RAY

from models.system_model_v3.model.state_variables.system import stability_fee
from models.system_model_v3.model.state_variables.historical_state import eth_price_df
from models.system_model_v3.model.state_variables.historical_state import liquidity_demand_pct_df, token_swap_pct_df


'''
See https://medium.com/reflexer-labs/introducing-proto-rai-c4cf1f013ef for current/launch values
'''

params = {
    # Admin parameters
    'debug': [False], # Print debug messages (see APT model)
    'raise_on_assert': [True], # See assert_log() in utils.py
    'free_memory_states': [['events', 'uniswap_oracle']],

    # Configuration options
    options.IntegralType.__name__: [options.IntegralType.LEAKY.value],

    # Exogenous states, loaded as parameter at every timestep - these are lambda functions, and have to be called
    'eth_trend': [0],
    'eth_price': [lambda run, timestep, trend, df=eth_price_df: 
                  df[str(run-1)].iloc[timestep] + (timestep/len(df[str(run-1)]) * (trend * df[str(run-1)].iloc[-1]))],
    'liquidity_demand_pct_events': [lambda run, timestep, df=liquidity_demand_pct_df: df[str(run-1)].iloc[timestep]],
    'token_swap_pct_events': [lambda run, timestep, df=token_swap_pct_df: df[str(run-1)].iloc[timestep]],
    'seconds_passed': [lambda timestep, df=None: 3600],
    
    'liquidity_demand_enabled': [False],
    'liquidity_demand_shock': [False], # introduce shocks (up to 50% of secondary market pool)
    'liquidity_demand_max_percentage': [0.1], # max percentage of secondary market pool when no shocks introduced using liquidity_demand_shock
    'liquidity_demand_shock_percentage': [0.5], # max percentage of secondary market pool when shocks introduced using liquidity_demand_shock

    # Time parameters
    'expected_blocktime': [15], # seconds
    'control_period': [3600 * 4], # seconds; must be multiple of cumulative time
    
    # Controller parameters
    'controller_enabled': [True],
    'enable_controller_time': [7 * 24 * 3600], # delay in enabling controller (7 days)
    'kp': [5e-8], # proportional term for the stability controller
    'ki': [0], # integral term for the stability controller
    'kd': [0],
    'khow': [0],
    'alpha': [0 * RAY], # in 1/RAY
    'error_term': [lambda target, measured: target - measured],
    'rescale_target_price': [False], # scale the target price by the liquidation ratio
    
    # APT model
    'arbitrageur_considers_liquidation_ratio': [True],
    'interest_rate': [1.03], # Real-world expected interest rate, for determining profitable arbitrage opportunities
    

    # APT OLS model
    # OLS values (Feb. 6, 2021) for beta_1 and beta_2
    'beta_1': [9.084809e-05],
    'beta_2': [-4.194794e-08],

    # CDP parameters
    'liquidation_ratio': [1.45], # Configure the liquidation ratio parameter e.g. 150%
    'liquidation_buffer': [2.0], # Configure the liquidation buffer parameter: the multiplier for the liquidation ratio, that users apply as a buffer
    'liquidation_penalty': [0], # Percentage added on top of collateral needed to liquidate CDP. This is needed in order to avoid auction grinding attacks.
    'debt_ceiling': [1e9],
    # redemption rate bounds used by rebalance and eth_leverage agents
    'max_redemption_rate': [50],
    'min_redemption_rate': [-50],

    # System parameters
    'stability_fee': [lambda timestep, df=None: stability_fee], # per second interest rate (x% per month)

    # Uniswap parameters
    'uniswap_fee': [0.003], # 0.3%
    'gas_price': [100e-9], # 100 gwei, current "fast" transaction
    'swap_gas_used': [103834],
    'cdp_gas_used': [(369e3 + 244e3) / 2], # Deposit + borrow; repay + withdraw

    # rate and price traders
    'trader_market_premium': [1.00],

    'rate_trader_count': [100],
    'rate_trader_mean_pct': [3],
    'rate_trader_min_pct': [1],
    'rate_trader_std_pct': [2 * (3-0)], 
    'rate_trader_mean_days': [0],
    'rate_trader_min_days': [0],
    'rate_trader_std_days': [2 * (0-0)],

    'price_trader_count': [100],
    'price_trader_mean_pct': [5],
    'price_trader_min_pct': [2],
    'price_trader_std_pct': [2 * (5-2)],

    #malicous pricing fixing whale parameters
    'malicious_whale_pump_percent': [1.05], #pump the price by 5%
    'malicious_whale_t1':[3600*24*15],#when the whale starts the attack 
    'malicious_whale_t2':[3600*24*30*1.8],#when the whale stops the attack
    'malicious_whale_kp': [200],

    # ETH leveragers. The file "liquidity.py" also contain liquidity parameters for the agent. The min needs to be higher than liquidation_ratio and max needs to be higher than min.
    'eth_leverager_target_min_liquidity_ratio': [2.9],
    'eth_leverager_target_max_liquidity_ratio': [2.9],
    
    # ETH leveragers external rates
    'malicious_rai_trader_max_balance': [100000],
    'malicious_rai_trader_p': [-10],

    # RAI APY Maximizers
    'base_rate_trader_max_APY_diff': [10],
    'rai_borrower_max_APY_diff': [5],
    'rai_lender_max_APY_diff': [5]

}
