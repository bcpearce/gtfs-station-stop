import time

from gtfs_station_stop.alert import Alert
from gtfs_station_stop.feed_subject import FeedSubject


class RouteStatus:
    def __init__(self, route_id: str, updater: FeedSubject):
        self.id = route_id
        self.updater = updater
        self.updater.subscribe(self)
        self.alerts: list[Alert] = []
        self._last_updated = None

    @property
    def last_updated(self):
        """Last update triggered by updater."""
        return self._last_updated

    def begin_update(self, timestamp: float | None):
        self.alerts.clear()
        self._last_updated = timestamp if timestamp is not None else time.time()
