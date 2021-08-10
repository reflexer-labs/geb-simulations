def rate_delta_to_delta(x_balance, y_balance, xy_rate_pct_delta):
    balance_pct = 1/(xy_rate_pct_delta + 1) - 1
    x_delta = x_balance * balance_pct

    return x_delta

print(rate_delta_to_delta(10000906.674484, 106767.954816, -0.31))
