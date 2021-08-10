# Experiments run

## V3 model


* Recommended params
[Raw resuls here:](reflexer/experiments/system_model_v3/recommended_params/experiment_run_log.md)
[Analysis here:](Single_run.ipynb)
Override params:
None
Result: 
Systems appears to be running as would be expected

* Query 1: does market price decline without controller?
[Raw resuls here:](reflexer/experiments/system_model_v3_Query_1/experiment_run_log.md)
[Analysis here:](Query_1.ipynb)
Override params:
```
sweeps = {
    'arbitrageur_considers_liquidation_ratio': [True,False],
    'rescale_target_price': [True, False]
}


params_override = {
    'controller_enabled': [False],
    'liquidity_demand_shock': [False],
}
```
Result: Implication from Reflexer: _controller_ is creating the market price decline--proceed with Query 2



* Query 2: does market price decline with controller, when $K_i = 0$?
[Raw resuls here:](reflexer/experiments/system_model_v3/Query_2/experiment_run_log.md)
[Analysis here:](Query_2_does_market_price_decline_with controller_when_K_i_equal_to_0?.ipynb)
Override params:
```
sweeps = {
    'arbitrageur_considers_liquidation_ratio': [True,False],
    'rescale_target_price': [True, False]

}

params_override = {
    'ki': [0],
}
```

Result: Market price declines


* Query 2.5: does market price decline with controller, when $K_i = 0$ and $\alpha = 0$?
[Raw resuls here:](reflexer/experiments/system_model_v3/Query_2/experiment_run_log.md)
[Analysis here:](Query_2_does_market_price_decline_with controller_when_K_i_equal_to_0?.ipynb)
Override params:
```
sweeps = {
    'arbitrageur_considers_liquidation_ratio': [True,False],
    'rescale_target_price': [True, False]

}

params_override = {
    'ki': [0],
}
```

Result: Market price declines



* Query 3: does market price decline with controller, when $K_i < 0$?
[Raw resuls here:](reflexer/experiments/system_model_v3/Query_3/experiment_run_log.md)
[Analysis here:](Query_3_does_market_price_decline_with_controller_when_K_i_less_than_0?.ipynb)
Override params:
```
sweeps = {
    'arbitrageur_considers_liquidation_ratio': [True,False],
    'rescale_target_price': [True, False]
}

```

Result: 

* Sanity check plot
[Raw resuls here:](reflexer/experiments/system_model_v3/sanity_check_plot/experiment_run_log.md)
[Analysis here:](Sanity_check.ipynb)
Override params:
```
params_override = {
    'controller_enabled': [False],
}
```
Result: 


* Unstable params
[Raw resuls here:](reflexer/experiments/system_model_v3/unstable_controller_params/experiment_run_log.md)
[Analysis here:](Unstable_Controller_Parameters.ipynb)
Override params:
```
params_override = {
    'kp': [-2e-7], # proportional term for the stability controller: units 1/USD
    'ki': [5e-9], # integral term for the stability controller scaled by control period: units 1/(USD*seconds)
}
```
Result: 
