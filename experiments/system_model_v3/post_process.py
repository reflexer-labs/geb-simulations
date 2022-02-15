from radcad.core import generate_parameter_sweep
import pandas as pd
import time
from models.utils.process_results import drop_dataframe_midsteps
from . import profits

def post_process_results(df, params=None, set_params=['kp', 'ki']):
    
    # Uncomment if drop_substeps radcad option not selected
    # print("Dropping midsteps")
    #df = drop_dataframe_midsteps(df)


    df.eval('eth_collateral_value = eth_collateral * eth_price', inplace=True)
    df.eval('collateralization_ratio = (eth_collateral * eth_price) / (principal_debt * target_price)', inplace=True)

    df.eval('apy = ((1 + target_rate) ** (60*60*24*356) - 1) * 100', inplace=True)

    # summarize some of agents' behavior
    df['rate_trader_total_base'], df['rate_trader_base'], df['rate_trader_total_rai_base'] = \
        zip(*df.apply(profits.rate_trader_balances, axis = 1))

    df['eth_leverager_total_base'], df['eth_leverager_collateral_base'], \
            df['eth_leverager_debt_base'], df['eth_leverager_collateral'], \
            df['eth_leverager_debt'] = zip(*df.apply(profits.eth_leverager_balances, axis=1))

    df['eth_leverager_cratio'] = df['eth_leverager_collateral_base'] / df['eth_leverager_debt_base']
    df['eth_leverager_collateral_diff'] = df['eth_leverager_collateral'].diff()

    if not params or not set_params:
        return df

    param_sweep = generate_parameter_sweep(params)
    param_sweep = [{param: subset[param] for param in set_params} for subset in param_sweep]

    # Assign parameters to subsets
    #print("Assigning parameters to subsets")
    for subset_index in df['subset'].unique():
        for (key, value) in param_sweep[subset_index].items():
            df.loc[df.eval(f'subset == {subset_index}'), key] = value
   
    # individual contributions of kp/ki to total rate
    df['kp_rate'] = df['kp'] * df['error_star']
    df['ki_rate'] = df['ki'] * df['error_star_integral']

    return df
