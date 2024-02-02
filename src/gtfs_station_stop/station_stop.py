import time

from gtfs_station_stop.feed_subject import FeedSubject


class StationStop:
    def __init__(self, stop_id: str, updater: FeedSubject):
        self.stop_id = stop_id
        self.updater = updater
        self.updater.subscribe(self)
        self.arrivals = []
        self.alerts = []
        self.last_updated = None

    def get_arrivals(self):
        return self.arrivals

    def get_time_to_arrivals(self):
        current_time = time.time()
        return [(id, (t - current_time)) for id, t in self.arrivals]

    def get_alerts(self):
        return self.alerts
