def rate_trader_balances(row):
    # How much BASE plus RAI in BASE is held
    traders = row['rate_traders']
    rp = row['target_price']
    
    total_base = 0
    base = 0
    total_rai_base = 0
    for trader in traders:
        total_base += trader['base_balance']
        total_base += trader['rai_balance'] * rp
        base += trader['base_balance']
        total_rai_base += trader['rai_balance'] * rp

    return total_base, base, total_rai_base

def price_trader_balances(row):
    # How much BASE plus RAI in BASE is held
    traders = row['price_traders']
    rp = row['target_price']
    
    total_base = 0
    base = 0
    total_rai_base = 0
    for trader in traders:
        total_base += trader['base_balance']
        total_base += trader['rai_balance'] * rp
        base += trader['base_balance']
        total_rai_base += trader['rai_balance'] * rp

    return total_base, base, total_rai_base

def eth_leverager_balances(row):
    eth_price = row['eth_price']
    rp = row['target_price']
    safes = row['cdps'] # SAFEs are initialized in timestep 1
    
    df = safes.query(f"open == 1 and owner == 'leverager'")
    total_collateral = df['locked'].sum() - df['freed'].sum() - df['v_bitten'].sum()
    total_debt = df['drawn'].sum() - df['wiped'].sum() - df['u_bitten'].sum()
    debt_base = total_debt * rp
    collateral_base = total_collateral * eth_price
    total_base = collateral_base - debt_base

    return total_base, collateral_base, debt_base, total_collateral, total_debt

"""
def eth_leverager_total_base(row):
    eth_price = row['eth_price']
    rp = row['target_price']
    safes = row['cdps'] # SAFEs are initialized in timestep 1
    
    collateral_base = 0
    debt_base = 0
    for index, cdp in safes.query(f"open == 1 and owner == 'leverager'").iterrows():
        locked = cdp["locked"]
        freed = cdp["freed"]
        drawn = cdp["drawn"]
        wiped = cdp["wiped"]
        dripped = cdp["dripped"]
        v_bitten = cdp["v_bitten"]
        u_bitten = cdp["u_bitten"]
        w_bitten = cdp["w_bitten"]
        
        collateral = locked - freed - v_bitten
        debt = drawn - wiped - u_bitten
        
        collateral_base += collateral * eth_price
        debt_base += debt * rp
        
    return collateral_base - debt_base

def eth_leverager_collateral_base(row):
    eth_price = row['eth_price']
    rp = row['target_price']
    safes = row['cdps'] # SAFEs are initialized in timestep 1
    
    collateral_base = 0
    for index, cdp in safes.query(f"open == 1 and owner == 'leverager'").iterrows():
        locked = cdp["locked"]
        freed = cdp["freed"]
        drawn = cdp["drawn"]
        wiped = cdp["wiped"]
        dripped = cdp["dripped"]
        v_bitten = cdp["v_bitten"]
        u_bitten = cdp["u_bitten"]
        w_bitten = cdp["w_bitten"]
        
        collateral = locked - freed - v_bitten
        collateral_base += collateral * eth_price
        
    return collateral_base

def eth_leverager_collateral(row):
    eth_price = row['eth_price']
    rp = row['target_price']
    safes = row['cdps'] # SAFEs are initialized in timestep 1
    
    collateral = 0
    for index, cdp in safes.query(f"open == 1 and owner == 'leverager'").iterrows():
        locked = cdp["locked"]
        freed = cdp["freed"]
        drawn = cdp["drawn"]
        wiped = cdp["wiped"]
        dripped = cdp["dripped"]
        v_bitten = cdp["v_bitten"]
        u_bitten = cdp["u_bitten"]
        w_bitten = cdp["w_bitten"]
        
        collateral = locked - freed - v_bitten
        collateral += collateral
        
    return collateral

def eth_leverager_debt_base(row):
    rp = row['target_price']
    safes = row['cdps'] # SAFEs are initialized in timestep 1
    
    debt_base = 0
    for index, cdp in safes.query(f"open == 1 and owner == 'leverager'").iterrows():
        locked = cdp["locked"]
        freed = cdp["freed"]
        drawn = cdp["drawn"]
        wiped = cdp["wiped"]
        dripped = cdp["dripped"]
        v_bitten = cdp["v_bitten"]
        u_bitten = cdp["u_bitten"]
        w_bitten = cdp["w_bitten"]
        
        debt = drawn - wiped - u_bitten
        debt_base += debt * rp
        
    return debt_base

def eth_leverager_debt(row):
    safes = row['cdps'] # SAFEs are initialized in timestep 1
    
    debt = 0
    for index, cdp in safes.query(f"open == 1 and owner == 'leverager'").iterrows():
        locked = cdp["locked"]
        freed = cdp["freed"]
        drawn = cdp["drawn"]
        wiped = cdp["wiped"]
        dripped = cdp["dripped"]
        v_bitten = cdp["v_bitten"]
        u_bitten = cdp["u_bitten"]
        w_bitten = cdp["w_bitten"]
        
        debt += drawn - wiped - u_bitten
        
    return debt
        
"""
def price_trader_profit(df, run):
    df_run = df.query(f'run == {run}')
    start_traders = df_run['price_traders'].iloc[1]
    start_rp = df_run['target_price'].iloc[1]
    
    end_traders = df_run['price_traders'].iloc[-1]
    end_rp = df_run['target_price'].iloc[-1]
    
    start_total_base = 0
    for trader in start_traders:
        start_total_base += trader['base_balance']
        start_total_base += trader['rai_balance'] * start_rp
        
    end_total_base = 0
    for trader in end_traders:
        end_total_base += trader['base_balance']
        end_total_base += trader['rai_balance'] * end_rp

    return end_total_base - start_total_base

def rate_trader_profit(df, run):
    df_run = df.query(f'run == {run}')
    start_traders = df_run['rate_traders'].iloc[1]
    start_rp = df_run['target_price'].iloc[1]
    
    final_traders = df_run['rate_traders'].iloc[-1]
    final_rp = df_run['target_price'].iloc[-1]
    
    start_total_base = 0
    start_total_rai = 0
    start_total_rai_base = 0
    start_base_only = 0
    for trader in start_traders:
        start_base_only += trader['base_balance']
        start_total_base += trader['base_balance']
        start_total_base += trader['rai_balance'] * start_rp
        start_total_rai += trader['rai_balance']
        start_total_rai_base += trader['rai_balance'] * start_rp
        
    final_total_base = 0
    final_total_rai = 0
    final_total_rai_base = 0
    final_base_only = 0
    n_trades = 0
    for trader in final_traders:
        final_base_only += trader['base_balance']
        final_total_base += trader['base_balance']
        final_total_base += trader['rai_balance'] * final_rp
        final_total_rai += trader['rai_balance']
        final_total_rai_base += trader['rai_balance'] * final_rp
        n_trades += trader['n_buys'] + trader['n_sells']
        
    return {'start_base_only': start_base_only,
            'start_total_rai': start_total_rai,
            'start_total_rai_base': start_total_rai_base,
            'start_total_base': start_total_base,
            'final_base_only': final_base_only,
            'final_total_rai': final_total_rai,
            'final_total_rai_base': final_total_rai_base,
            'final_total_base': final_total_base,
            'n_trades': n_trades,
            'profit': final_total_base - start_total_base,
            'profit_per_trade': (final_total_base - start_total_base)/n_trades
            
           }
            
    
def cdp_profit(df, owner, run):
    df_run = df.query(f'run == {run}')
    start_eth_price = df_run['eth_price'].iloc[0]
    start_rp = df_run['target_price'].iloc[0]
    start_safes = df_run['cdps'].iloc[1] # SAFEs are initialized in timestep 1
    
    final_eth_price = df_run['eth_price'].iloc[-1]
    final_rp = df_run['target_price'].iloc[-1]
    final_safes = df_run['cdps'].iloc[-1]

    start_base = 0
    start_collateral = 0
    start_collateral_base = 0
    start_debt = 0
    start_debt_base = 0
    for index, cdp in start_safes.query(f"open == 1 and owner == '{owner}'").iterrows():
        locked = cdp["locked"]
        freed = cdp["freed"]
        drawn = cdp["drawn"]
        wiped = cdp["wiped"]
        dripped = cdp["dripped"]
        v_bitten = cdp["v_bitten"]
        u_bitten = cdp["u_bitten"]
        w_bitten = cdp["w_bitten"]
        
        collateral = locked - freed - v_bitten
        debt = drawn - wiped - u_bitten
        
        start_collateral += collateral
        start_debt += debt
        
        collateral_base = collateral * start_eth_price
        debt_base = debt * start_rp
        
        #print(f"start {collateral_base=}, {collateral=}, {start_eth_price=}")
        
        start_collateral_base += collateral_base       
        start_debt_base += debt_base    
        start_base += collateral_base - debt_base

    final_base = 0
    final_collateral = 0
    final_collateral_base = 0
    final_debt = 0
    final_debt_base = 0
    for index, cdp in final_safes.query(f"open == 1 and owner == '{owner}'").iterrows():
        locked = cdp["locked"]
        freed = cdp["freed"]
        drawn = cdp["drawn"]
        wiped = cdp["wiped"]
        dripped = cdp["dripped"]
        v_bitten = cdp["v_bitten"]
        u_bitten = cdp["u_bitten"]
        w_bitten = cdp["w_bitten"]
        
        collateral = locked - freed - v_bitten
        debt = drawn - wiped - u_bitten 
        
        final_collateral += collateral
        final_debt += debt
        collateral_base = collateral * final_eth_price
        debt_base = debt * final_rp
        
        #print(f"final {collateral_base=}, {collateral=}, {final_eth_price=}")
        final_collateral_base += collateral_base
        final_debt_base += debt_base

        final_base += collateral_base - debt_base

    return {"start_collateral": start_collateral,
            "start_collateral_base": start_collateral_base, 
            "start_debt": start_debt,
            "start_debt_base": start_debt_base,   
            "final_collateral": final_collateral,           
            "final_collateral_base": final_collateral_base,
            "final_debt": final_debt,
            "final_debt_base": final_debt_base,
            "final_new_debt": final_debt - start_debt,
            "final_new_debt_base": final_debt_base - start_debt_base,
            "start_base": start_base,
            "final_base": final_base,
            "profit": final_collateral_base - start_collateral_base - final_debt_base + start_debt_base
           }
