from models.system_model_v3.model.state_variables.liquidity import cdps, uniswap_rai_balance, uniswap_eth_balance
from models.system_model_v3.model.state_variables.liquidity import price_trader_rai_balance, price_trader_base_balance
from models.system_model_v3.model.state_variables.liquidity import rate_trader_rai_balance, rate_trader_base_balance
from models.system_model_v3.model.state_variables.liquidity import liquidity_cdp_eth_collateral, liquidity_cdp_rai_balance
from models.system_model_v3.model.state_variables.liquidity import liquidity_cdp_count
from models.system_model_v3.model.state_variables.liquidity import arbitrage_cdp_eth_collateral
from models.system_model_v3.model.state_variables.liquidity import malicious_whale_eth_balance, malicious_whale_rai_balance, malicious_rai_trader_balance
from models.system_model_v3.model.state_variables.liquidity import eth_leverager_rai_balance, eth_leverager_eth_balance
from models.system_model_v3.model.state_variables.liquidity import base_rate_trader_balance, rai_borrower_balance, rai_lender_balance
from models.system_model_v3.model.state_variables.system import stability_fee, target_price
from models.system_model_v3.model.state_variables.historical_state import eth_price
from models.system_model_v3.model.parts.uniswap_oracle import UniswapOracle

import datetime as dt

# NB: These initial states may be overriden in the relevant notebook or experiment process
state_variables = {
    # Metadata / metrics
    'cdp_metrics': {},
    'optimal_values': {},
    'sim_metrics': {},
    
    # Time states
    'timedelta': 0, # seconds
    'cumulative_time': 0, # seconds
    'timestamp': dt.datetime.strptime('2018-01-01', '%Y-%m-%d'), # type: datetime; start time
    'blockheight': 0, # block offset (init 0 simplicity)
    
    # Exogenous states
    'eth_price': eth_price, # unit: dollars; updated from historical data as exogenous parameter
    'liquidity_demand': 1,
    'liquidity_demand_mean': 1, # net transfer in or out of RAI tokens in the ETH-RAI pool
    
    # CDP states
    'cdps': cdps, # A dataframe of CDPs (both open and closed)
    # ETH collateral states
    'eth_collateral': 0, # "Q"; total ETH collateral in the CDP system i.e. locked - freed - bitten
    'eth_locked': 0, # total ETH locked into CDPs
    'eth_freed': 0, # total ETH freed from CDPs
    'eth_bitten': 0, # total ETH bitten/liquidated from CDPs

    # Liquidity CDPs
    'liquidity_cdp_eth_collateral': liquidity_cdp_eth_collateral,
    'liquidity_cdp_rai_balance': liquidity_cdp_rai_balance,
    'liquidity_cdp_count': liquidity_cdp_count,

    # Arbitrage CDP
    'arbitrage_cdp_eth_collateral': arbitrage_cdp_eth_collateral,
    
    # Principal debt states
    'principal_debt': 0, # "D_1"; the total debt in the CDP system i.e. drawn - wiped - bitten
    'rai_drawn': 0, # total RAI debt minted from CDPs
    'rai_wiped': 0, # total RAI debt wiped/burned from CDPs in repayment
    'rai_bitten': 0, # total RAI liquidated from CDPs
    
    # Accrued interest states
    'accrued_interest': 0, # "D_2"; the total interest accrued in the system i.e. current D_2 + w_1 - w_2 - w_3
    'interest_dripped': 0, # cumulative w_1 interest collected
    'interest_wiped': 0, # cumulative w_2, interest repaid - in practice acrues to MKR holders, because interest is actually acrued by burning MKR
    'interest_bitten': 0, # cumulative w_3
    'w_1': 0, # discrete "drip" event, in RAI
    'w_2': 0, # discrete "shut"/"wipe" event, in RAI
    'w_3': 0, # discrete "bite" event, in RAI
    'system_revenue': 0, # "R"; value accrued by protocol token holders as result of contracting supply
    
    # System states
    'stability_fee': stability_fee, # interest rate used to calculate the accrued interest; per second interest rate (1.5% per month)
    'market_price': target_price, # unit: dollars; the secondary market clearing price
    'market_price_twap': 0,
    'target_price': target_price, # unit: dollars; equivalent to redemption price
    'target_rate': 0 / (30 * 24 * 3600), # per second interest rate (X% per month), updated by controller
    
    # APT model states
    'eth_return': 0,
    'eth_gross_return': 0,
    'expected_market_price': target_price, # root of non-arbitrage condition
    'expected_debt_price': target_price, # predicted "debt" price, the intrinsic value of RAI according to the debt market activity and state
    
    # Price trader
    'price_trader_rai_balance': price_trader_rai_balance,
    'price_trader_base_balance': price_trader_base_balance,
    'price_traders': [], # price traders are initialized in price_traders.py
    
    # Rate trader
    'rate_trader_rai_balance': rate_trader_rai_balance,
    'rate_trader_base_balance': rate_trader_base_balance,
    'rate_traders': [], # rate traders are initialized in price_traders.py
   
    # Controller states
    'error_star': 0, # price units
    'prev_error_star': 0, # price units
    'error_star_integral': 0, # price units x seconds
    
    # Uniswap states
    'market_slippage': 0,
    'RAI_balance': uniswap_rai_balance,
    'ETH_balance': uniswap_eth_balance,
    'UNI_supply': uniswap_rai_balance,
    'uniswap_oracle': UniswapOracle(
        window_size=16*3600, # 16 hours
        max_window_size=24*3600, # 24 hours
        granularity=4 # period = window_size / granularity
    ),

    # price pump whale
    'malicious_whale_funds_eth': malicious_whale_eth_balance,
    'malicious_whale_funds_rai': malicious_whale_rai_balance,
    'malicious_whale_state': 0, #0 when the whale has not started, 1 after the whale has started
    'malicious_whale_p0': 0, #price of RAI which the whale considers as the non-pumped price (set by the whale when it starts)
    
    'eth_leverager_rai_balance': eth_leverager_rai_balance,
    'eth_leverager_eth_balance': eth_leverager_eth_balance,
    
    # malicious rai trader state
    'malicious_rai_trader_state': 0, #max amount of balance the trader can go long or short
    'malicious_rai_trader_max_balance': malicious_rai_trader_balance,

    # external RAI and BASE interest rates
    'external_BASE_APY': 5, #External interest rate that agents can use to get constant 5% return over year for their BASE balance
    'compound_RAI_borrow_APY': 5, #Yearly interest rate that agents need to pay to borrow RAI
    'compound_RAI_lend_APY': 3, #Yearly interest rate that agents get to loan RAI

    #Base rate trader
    'base_rate_trader_state': 0, #BASE rate trader state, varies between [-base_rate_trader_max_balance,base_rate_trader_max_balance]. It represent how much RAI the agent is SHORT at the moment
    'base_rate_trader_max_balance': base_rate_trader_balance, #max amount of balance the trader can go long or short

    #RAI Borrower
    'rai_borrower_state': 0, #Rai borrowers state, varies between [-rai_borrower_max_balance,rai_borrower_max_balance]. It represent how much RAI the agent is SHORT at the moment
    'rai_borrower_max_balance': rai_borrower_balance, #Max amount of balance the trader can go long or short

    #RAI Lender
    'rai_lender_state': 0, #Rai lenders state, varies between [-rai_lender_max_balance,rai_lender_max_balance]. It represent how much RAI the agent is SHORT at the moment
    'rai_lender_max_balance': rai_lender_balance #Max amount of balance the trader can go long or short
}
