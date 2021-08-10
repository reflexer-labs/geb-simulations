from models.system_model_v3.model.parts.utils import apy_to_target_rate
# Set the initial target price, in Dollars
target_price = 3.14
# per second interest rate (x% per month)
stability_fee = (0.005 * 30 / 365) / (30 * 24 * 3600) 
# 6.279371924910298e-10
stability_fee = apy_to_target_rate(2)
