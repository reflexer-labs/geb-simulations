from collections import namedtuple, deque
import math

ChainlinkObservation = namedtuple('ChainlinkObservation', ['timestamp', 'time_adjusted_price', 'price'])

class ChainlinkTWAP():
    def __init__(self, granularity=3, window_size=24*3600, max_window_size=4*24*3600):
        self.default_amount_in = 1
        self.target_token = 'rai'
        self.denomination_token = 'eth'

        self.granularity = granularity
        self.window_size = window_size
        self.max_window_size = max_window_size

        self.last_update_time = 0
        self.updates = 0
        self.period_size = window_size / granularity
        self.median_price = 0
        
        self.chainlink_observations = deque([], granularity)
        self.converter_price_cumulative = 0

        self.price_0_cumulative = 0
        self.price_1_cumulative = 0

        self.link_aggregator_timestamp = 0

        assert self.granularity > 1
        assert self.window_size > 0
        assert self.max_window_size > self.window_size
        assert self.period_size == self.window_size / self.granularity
        assert int(self.window_size / self.granularity) * self.granularity == self.window_size

    def earliest_observation_index(self):
        if (self.updates <= self.granularity):
            return 0
        else:
            return self.updates - int(self.granularity)

    def update_observations(self, state, time_elapsed_since_latest, new_result):
        now = state['cumulative_time']
        new_time_adjusted_price = new_result * time_elapsed_since_latest
        #print(f"update_obs() {new_result=}, {time_elapsed_since_latest=}, {new_time_adjusted_price=}")

        self.converter_price_cumulative += new_time_adjusted_price

        #if self.updates >= self.granularity: # if len(self.chainlink_observations) >= self.granularity: ?????
        if len(self.chainlink_observations) >= self.granularity:
            #print(f"update_obs() subtracting {self.chainlink_observations[0].time_adjusted_price}")
            self.converter_price_cumulative -= self.chainlink_observations[0].time_adjusted_price
            
        self.chainlink_observations.append(
            ChainlinkObservation(now, new_time_adjusted_price, new_result)
        )
        #print(f"update_obs() final {self.converter_price_cumulative=}")

    def update_result(self, state):
        #print(f"update_result() {state}")
        now = state['cumulative_time']

        last_update_time = self.last_update_time
        elapsed_time = self.period_size if len(self.chainlink_observations) == 0 else now - self.chainlink_observations[-1].timestamp
        
        if len(self.chainlink_observations) > 0 and not elapsed_time >= self.period_size:
            return

        aggregator_result = state['market_price']
        aggregator_timestamp = state['market_price_timestamp']

        #require(aggregatorResult > 0, "ChainlinkTWAP/invalid-feed-result");
        if aggregator_result <= 0:
            raise ValueError("ChainlinkTWAP/invalid-feed-result")

        #require(both(aggregatorTimestamp > 0, aggregatorTimestamp > linkAggregatorTimestamp), "ChainlinkTWAP/invalid-timestamp");
        if aggregator_timestamp <= self.link_aggregator_timestamp:
            return

        time_since_first = now - self.last_update_time if len(self.chainlink_observations) == 0 else now - self.chainlink_observations[0].timestamp

        self.update_observations(state, elapsed_time, aggregator_result)

        self.median_price = self.converter_price_cumulative / time_since_first
        self.last_update_time = now
        self.updates += 1
        self.link_aggregator_timestamp = aggregator_timestamp
