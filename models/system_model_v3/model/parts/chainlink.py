class ChainlinkFeed():
    def __init__(self, staleness, deviation_threshold):
        self.staleness = staleness
        self.deviation_threshold = deviation_threshold

