import time

from gtfs_station_stop.alert import Alert
from gtfs_station_stop.arrival import Arrival
from gtfs_station_stop.feed_subject import FeedSubject


class StationStop:
    def __init__(self, stop_id: str, updater: FeedSubject):
        self.id = stop_id
        self.updater = updater
        self.updater.subscribe(self)
        self.arrivals: list[Arrival] = []
        self.alerts: list[Alert] = []
        self._last_updated = None

    @property
    def last_updated(self):
        return self._last_updated

    def begin_update(self, timestamp: float | None = None):
        if timestamp is None:
            timestamp = time.time()
        self.alerts.clear()
        self.arrivals.clear()
        self._last_updated = timestamp

    def get_time_to_arrivals(self, the_time: float | None = None):
        if the_time is None:
            the_time = time.time()
        return [Arrival(a.time - the_time, a.route, a.trip) for a in self.arrivals]
