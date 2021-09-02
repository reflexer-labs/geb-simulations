def get_input_price(dx, x_balance, y_balance, trade_fee=0.003):
    '''
    How much y received for selling dx?
    Example:
    new_x = (1 + alpha)*x_balance
    new_y = y_balance - dy
    '''
    rho = trade_fee
    
    alpha = dx / x_balance
    gamma = 1 - rho
    
    dy = (alpha * gamma / (1 + alpha * gamma)) * y_balance
    
    _dx = alpha * x_balance
    _dy = -dy
    
    return (_dx, _dy)

def get_output_price(dy, x_balance, y_balance, trade_fee=0.003):
    '''
    How much x needs to be sold to buy dy?
    Example:
    new_x = x_balance + dx
    new_y = (1 - beta)*y_balance
    '''
    rho = trade_fee
    
    beta = dy / y_balance
    gamma = 1 - rho
    
    dx = (beta / (1 - beta)) * (1 / gamma) * x_balance
    
    _dx = dx
    _dy = -beta * y_balance
    
    return (_dx, _dy)

def buy_to_price(eth_balance, rai_balance, goal_price, market_price):
    '''
    How much RAI to buy to achieve a goal market price?
    '''
    a = rai_balance * ((market_price/goal_price)**(1/2) - 1)

    # if a is positive, we're already past our goal price
    return max(-a,0)
