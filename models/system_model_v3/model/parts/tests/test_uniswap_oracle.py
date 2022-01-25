import copy
import time
import pytest
from uniswap_oracle import UniswapOracle
import random
import numpy as np

"""
cumulative_times = list(range(0, 40000000, 3600))
rai_balances = [random.randint(1000, 1000000) for _ in range(len(cumulative_times))]
eth_balances = [random.randint(1000, 1000000) for _ in range(len(cumulative_times))]
eth_prices = [random.randint(100, 1000) for _ in range(len(cumulative_times))]
"""
cumulative_times = [3600, 7200, 10800, 14400, 18000, 21600, 25200, 28800, 32400, 36000, 39600, 43200, 46800, 50400, 54000, 57600, 61200, 64800]
data = [(106777.60615294595, 10000000.0, 294.06915111978924),
(106777.60615294595, 10000000.0, 291.20825197288093),
(107829.77125388513, 9902713.387786027, 292.28779175988126),
(107432.70166036802, 9939423.793583082, 289.3436976368749),
(108529.12684369899, 9839308.085702961, 286.8277709669044),
(109483.96096803086, 9753752.471984554, 286.2638800521939),
(109700.27459873691, 9734577.019116981, 283.65219150289414),
(110713.36406101282, 9645764.964559246, 283.68268645595685),
(110701.49843970363, 9646801.96395026, 284.46543843912633),
(110397.79695795586, 9673419.920311505, 283.4488014844647),
(110794.94874022203, 9638848.563513609, 287.3703467424073),
(109287.48047376894, 9772203.09060391, 285.964929771784),
(109826.20614830006, 9724411.033352356, 284.82012467687724),
(110268.96953894282, 9685481.241140306, 287.6220371203736),
(109197.95943275356, 9780761.974696577, 288.7495108956619),
(108772.8507647438, 9819102.404863937, 288.0325865337643),
(109044.40530388973, 9794722.956725033, 286.11984995085186),
(109775.57032337232, 9729679.18808664, 286.15691766760153)]

eth_balances = [x[0] for x in data]
rai_balances = [x[1] for x in data]
eth_prices = [x[2] for x in data]

#@pytest.mark.skip('tmp')
class TestUniswapOracle:
    def test_deepcopy_speed(self):
        o = UniswapOracle()

        states = [{'RAI_balance': rai_balances[i], 'ETH_balance': eth_balances[i],
                   'eth_price': eth_prices[i], 'cumulative_time': cumulative_times[i]} for i in range(len(cumulative_times))]
        s = time.time()
        for state in states:
            o.update_result(state)
            copy.deepcopy(o)
        print(f"took {time.time() - s} secs")

    def test_median(self):
        o = UniswapOracle(granularity=4, window_size=16*3600, max_window_size=21*3600)

        states = [{'RAI_balance': rai_balances[i], 'ETH_balance': eth_balances[i],
                   'eth_price': eth_prices[i], 'cumulative_time': cumulative_times[i]} for i in range(len(cumulative_times))]
        for i, state in enumerate(states):
            rai_usd = state['ETH_balance'] / state['RAI_balance'] * state['eth_price']
            o.update_result(state)
            #print(o.converter_feed_observations)
            #print(o.uniswap_observations)
            print(f"{i=}, {rai_usd=}, {o.median_price=}")

