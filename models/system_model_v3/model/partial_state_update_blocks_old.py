import models.system_model_v3.model.parts.markets as markets
import models.system_model_v3.model.parts.uniswap as uniswap
import models.system_model_v3.model.parts.init as init

from .parts.utils import s_update_sim_metrics, p_free_memory, s_collect_events
from .parts.governance import p_enable_controller

from .parts.controllers import *
from .parts.debt_market import *
from .parts.time import *
from .parts.apt_model import *
from .parts.price_traders import *
from .parts.rate_traders import *
from .parts.eth_leveragers import *
from .parts.malicious_whale_agents import p_constant_price_agent, s_store_malicious_whale_funds_eth, s_store_malicious_whale_funds_eth, s_store_malicious_whale_funds_rai, s_store_malicious_whale_state, s_store_malicious_whale_p0, p_malicious_rai_trader_external_funding, s_store_malicious_rai_trader_state
from .parts.moneymarket_agents import p_rai_lender, s_store_rai_lender_state, p_rai_borrower, s_store_rai_borrower_state, p_base_rate_trader, s_store_base_rate_trader_state

partial_state_update_blocks_unprocessed = [
    {
        'enabled': True,
        'policies': {
            'free_memory': p_free_memory,
            'random_seed': init.initialize_seed,
        },
        'variables': {
            'target_price': init.initialize_target_price,
        }
    },
    #################################################################
    {
        'details': '''
            This block observes (or samples from data) the amount of time passed between events
        ''',
        'enabled': True,
        'policies': {
            'time_process': resolve_time_passed
        },
        'variables': {
            'timedelta': store_timedelta,
            'timestamp': update_timestamp,
            'cumulative_time': update_cumulative_time
        }
    },
    #################################################################
    {
        'details': '''
            Exogenous ETH price process
        ''',
        'enabled': True,
        'policies': {
            'exogenous_eth_process': p_resolve_eth_price,
        },
        'variables': {
            'eth_price': s_update_eth_price,
            'eth_return': s_update_eth_return,
            'eth_gross_return': s_update_eth_gross_return
        }
    },
    #################################################################
    {   
        'details': '''
            Exogenous u,v activity: liquidate CDPs
        ''',
        'enabled': False,
        'policies': {
            'liquidate_cdps': p_liquidate_cdps
        },
        'variables': {
            'cdps': s_store_cdps,
        }
    },
    #################################################################
    {
        'details': '''
            Exogenous liquidity demand process
        ''',
        'enabled': True,
        'policies': {
            'liquidity_demand': markets.p_liquidity_demand
        },
        'variables': {
            'RAI_balance': uniswap.update_RAI_balance,
            'ETH_balance': uniswap.update_ETH_balance,
            'UNI_supply': uniswap.update_UNI_supply,
            'liquidity_demand': markets.s_liquidity_demand,
            'liquidity_demand_mean': markets.s_liquidity_demand_mean,
            'market_slippage': markets.s_slippage,
        }
    },
    #################################################################
    {
        'details': '''
            Resolve expected price and store in state
        ''',
        'enabled': False,
        'policies': {
            'market': p_resolve_expected_market_price
        },
        'variables': {
            'expected_market_price': s_store_expected_market_price
        }
    },
    #################################################################
    {
        'details': """
            APT model
        """,
        'enabled': False,
        'policies': {
            'arbitrage': p_arbitrageur_model
        },
        'variables': {
            'cdps': s_store_cdps,
            'optimal_values': s_store_optimal_values,
            'RAI_balance': uniswap.update_RAI_balance,
            'ETH_balance': uniswap.update_ETH_balance,
            'UNI_supply': uniswap.update_UNI_supply,
        }
    },
    #################################################################
    {
        'details': """
            rate trading model
        """,
        'enabled': True,
        'policies': {
            'trade_rate': p_trade_rate
        },
        'variables': {
            'rate_traders': s_store_rate_traders,
            'RAI_balance': uniswap.update_RAI_balance,
            'ETH_balance': uniswap.update_ETH_balance,
            'UNI_supply': uniswap.update_UNI_supply,
        }

    },
    #################################################################
    {
        'details': """
            price trading model
        """,
        'enabled': False,
        'policies': {
            'trade_price': p_trade_price
        },
        'variables': {
            'price_traders': s_store_price_traders,
            'RAI_balance': uniswap.update_RAI_balance,
            'ETH_balance': uniswap.update_ETH_balance,
            'UNI_supply': uniswap.update_UNI_supply,
        }
    },
    #################################################################
    {
        'details': """
            Malicius whale agent
        """,
        'enabled': False,
        'policies': {
            'arbitrage': p_constant_price_agent
        },
        'variables': {
            'malicious_whale_funds_eth': s_store_malicious_whale_funds_eth,
            'malicious_whale_funds_rai': s_store_malicious_whale_funds_rai,
            'malicious_whale_state': s_store_malicious_whale_state,
            'malicious_whale_p0': s_store_malicious_whale_p0,
            'RAI_balance': uniswap.update_RAI_balance,
            'ETH_balance': uniswap.update_ETH_balance
        }
    },
    #################################################################
    {
        'details': """
            RAI Borrower
        """,
        'enabled': False,
        'policies': {
            'arbitrage': p_rai_borrower,
        },
        'variables': {
            'rai_borrower_state': s_store_rai_borrower_state,
            'RAI_balance': uniswap.update_RAI_balance,
            'ETH_balance': uniswap.update_ETH_balance
        }
    },
    #################################################################
    {
        'details': """
            RAI Lender
        """,
        'enabled': False,
        'policies': {
            'arbitrage': p_rai_lender
        },
        'variables': {
            'rai_lender_state': s_store_rai_lender_state,
            'RAI_balance': uniswap.update_RAI_balance,
            'ETH_balance': uniswap.update_ETH_balance
        }
    },
    #################################################################
    {
        'details': """
            Base rate trader
        """,
        'enabled': False,
        'policies': {
            'arbitrage': p_base_rate_trader
        },
        'variables': {
            'base_rate_trader_state': s_store_base_rate_trader_state,
            'RAI_balance': uniswap.update_RAI_balance,
            'ETH_balance': uniswap.update_ETH_balance
        }
    },
    #################################################################
    {
        'details': """
            Malicious RAI Trader External Funding
        """,
        'enabled': False,
        'policies': {
            'arbitrage': p_malicious_rai_trader_external_funding
        },
        'variables': {
            'malicious_rai_trader_state': s_store_malicious_rai_trader_state,
            'RAI_balance': uniswap.update_RAI_balance,
            'ETH_balance': uniswap.update_ETH_balance,
            'UNI_supply': uniswap.update_UNI_supply,
        }
    },
    #################################################################
    {
        'details': """
            eth leverager
        """,
        'enabled': True,
        'policies': {
            'arbitrage': p_leverage_eth
        },
        'variables': {
            'cdps': s_store_cdps,
            'RAI_balance': uniswap.update_RAI_balance,
            'ETH_balance': uniswap.update_ETH_balance,
            'UNI_supply': uniswap.update_UNI_supply,
        }
    },
    #################################################################
    {
        'details': '''
            Endogenous w activity
        ''',
        'enabled': True,
        'policies': {},
        'variables': {
            'accrued_interest': s_update_accrued_interest,
            'cdps': s_update_cdp_interest
        }
    },
    #################################################################
    {
        'details': """
        Rebalance CDPs using wipes and draws 
        """,
        'enabled': True,
        'policies': {
            'rebalance_cdps': p_rebalance_cdps,
        },
        'variables': {
            'cdps': s_store_cdps,
            'RAI_balance': uniswap.update_RAI_balance,
            'ETH_balance': uniswap.update_ETH_balance,
            'UNI_supply': uniswap.update_UNI_supply,
        }
    },
    #################################################################
    {
        'enabled': True,
        'policies': {
            'market_price': markets.p_market_price
        },
        'variables': {
            'market_price': markets.s_market_price,
            'market_price_twap': markets.s_market_price_twap,
            'uniswap_oracle': markets.s_uniswap_oracle
        }
    },
    #################################################################
    {
        'details': """
        This block computes and stores the error terms
        required to compute the various control actions
        """,
        'enabled': True,
        'policies': {
            'observe': observe_errors
        },
        'variables': {
            'error_star': store_error_star,
            'prev_error_star': store_prev_error_star,
            'error_star_integral': update_error_star_integral,
        }
    },
    #################################################################
    {
        'details': """
        This block computes the stability control action 
        """,
        'enabled': True,
        'policies': {
            'governance': p_enable_controller,
        },
        'variables': {
            'target_rate': update_target_rate,
        }
    },
    #################################################################
    {
        'details': """
        This block updates the target price based on stability control action 
        """,
        'enabled': True,
        'policies': {},
        'variables': {
            'target_price': update_target_price,
        }
    },
    #################################################################
    {
        'details': """
           Aggregate interest activity
        """,
        'enabled': True,
        'policies': {},
        'variables': {
            'w_1': s_aggregate_w_1,
            'w_2': s_aggregate_w_2,
            'w_3': s_aggregate_w_3,
        }
    },
    #################################################################
    {
        'details': '''
            Update debt market state
        ''',
        'enabled': True,
        'policies': {},
        'variables': {
            'eth_collateral': s_update_eth_collateral,
            'principal_debt': s_update_principal_debt,
            'stability_fee': s_update_stability_fee,
        }
    },
    #################################################################
    {
        'details': '''
            Aggregate states
        ''',
        'enabled': True,
        'policies': {},
        'variables': {
            'eth_locked': s_update_eth_locked,
            'eth_freed': s_update_eth_freed,
            'eth_bitten': s_update_eth_bitten,
            'rai_drawn': s_update_rai_drawn,
            'rai_wiped': s_update_rai_wiped,
            'rai_bitten': s_update_rai_bitten,
            'accrued_interest': s_update_interest_bitten,
            'system_revenue': s_update_system_revenue,
        }
    },
    #################################################################
    {
        'details': '''
            Update cdp metrics 
        ''',
        'enabled': True,
        'policies': {},
        'variables': {
            'cdp_metrics': s_update_cdp_metrics,
        }
    },
]

partial_state_update_blocks = list(filter(lambda psub: psub.get('enabled', True), partial_state_update_blocks_unprocessed))
