import copy
import time
import pytest
from chainlink_twap import ChainlinkTWAP
import random
import numpy as np

"""
cumulative_times = list(range(0, 400000, 3600))
rai_prices = np.round([random.uniform(2.5, 3.5) for _ in range(len(cumulative_times))], 2)
#print(','.join(map(str, cumulative_times)))
#print(','.join(map(str, rai_prices)))
"""

n_updates = 40
cumulative_times = [0,3600,7200,10800,14400,18000,21600,25200,28800,32400,36000,39600,43200,46800,50400,54000,57600,61200,64800,68400,72000,75600,79200,82800,86400,90000,93600,97200,100800,104400,108000,111600,115200,118800,122400,126000,129600,133200,136800,140400,144000,147600,151200,154800,158400,162000,165600,169200,172800,176400,180000,183600,187200,190800,194400,198000,201600,205200,208800,212400,216000,219600,223200,226800,230400,234000,237600,241200,244800,248400,252000,255600,259200,262800,266400,270000,273600,277200,280800,284400,288000,291600,295200,298800,302400,306000,309600,313200,316800,320400,324000,327600,331200,334800,338400,342000,345600,349200,352800,356400,360000,363600,367200,370800,374400,378000,381600,385200,388800,392400,396000,399600][:n_updates]
rai_prices = [2.87,2.79,2.63,2.51,3.19,3.26,2.9,2.86,2.76,3.4,3.23,2.75,2.97,2.6,2.82,2.86,3.33,2.52,3.45,2.57,3.5,2.51,3.08,3.34,2.61,2.72,3.05,3.38,3.28,3.37,2.56,3.07,3.03,3.45,3.43,2.93,3.19,2.83,3.4,2.73,2.95,2.73,2.68,2.74,2.57,2.56,2.64,3.2,2.8,2.76,2.8,3.3,2.9,2.64,3.46,3.38,3.01,3.47,2.74,3.07,3.38,2.72,3.03,2.64,2.76,3.16,2.51,2.59,3.0,2.69,2.69,2.74,2.98,3.4,3.25,3.45,2.9,2.56,3.3,3.14,2.67,2.54,2.58,2.6,2.86,3.14,2.76,2.53,2.58,3.01,2.95,2.65,2.67,3.21,2.81,2.84,3.13,3.29,2.64,2.69,2.71,2.69,2.76,3.03,2.71,2.53,2.84,2.57,2.6,2.59,2.74,3.48][:n_updates]

#@pytest.mark.skip('tmp')
class TestChainlinkTWAP:
    def _test_deepcopy_speed(self):
        twap = ChainlinkTWAP(granularity=4, window_size=16*3600, max_window_size=21*3600)

        states = [{'market_price_timestamp': cumulative_times[i],
                   'market_price': rai_prices[i], 'cumulative_time': cumulative_times[i]} for i in range(len(cumulative_times))]
        s = time.time()
        for state in states:
            twap.update_result(state)
            copy.deepcopy(twap)
        print(f"took {time.time() - s} secs")

    def test_median(self):
        twap = ChainlinkTWAP(granularity=4, window_size=16*3600, max_window_size=21*3600)

        states = [{'market_price_timestamp': cumulative_times[i],
                   'market_price': rai_prices[i], 'cumulative_time': cumulative_times[i]} for i in range(len(cumulative_times))]
        for i, state in enumerate(states):
            #rai_usd = state['ETH_balance'] / state['RAI_balance'] * state['eth_price']
            #print(f"{i=}, new state {state}")
            twap.update_result(state)
            print(f"{i=}, {twap.chainlink_observations}, {twap.median_price=}")

