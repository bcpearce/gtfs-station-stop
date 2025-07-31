"""Station Stop."""

import datetime
import time
from copy import copy
from typing import TYPE_CHECKING

from gtfs_station_stop.arrival import Arrival
from gtfs_station_stop.feed_subject import FeedSubject
from gtfs_station_stop.stop_times import StopTimesDataset
from gtfs_station_stop.updatable import Updatable

if TYPE_CHECKING:
    from gtfs_station_stop.alert import Alert


class StationStop(Updatable):
    """Station Stop."""

    def __init__(self, stop_id: str, updater: FeedSubject) -> None:
        super().__init__()
        self.id = stop_id
        self.updater = updater
        self.updater.subscribe(self)
        self.arrivals: list[Arrival] = []
        self.alerts: list[Alert] = []

    def begin_update(self, timestamp: float | None = None) -> None:
        if timestamp is None:
            timestamp = time.time()
        self.alerts.clear()
        self.arrivals.clear()
        self._last_updated = timestamp

    def get_time_to_arrivals(
        self,
        the_time: float | None = None,
        *,
        stop_times_dataset: StopTimesDataset | None = None,
    ) -> list[Arrival]:
        """Get Time To Arrivals."""
        if the_time is None:
            the_time = time.time()

        def _make_relative_arrival(arrival: Arrival) -> Arrival:
            def _merge_today_with_stop_time(arrival: Arrival, delay) -> float:
                arrival_dt = datetime.datetime.today()
                if (
                    st := stop_times_dataset.get(arrival.trip, arrival.stop_sequence)
                ) is not None:
                    tmp_dt = datetime.datetime(
                        year=arrival_dt.year,
                        month=arrival_dt.month,
                        day=arrival_dt.day,
                        hour=st.arrival_time.hour,
                        minute=st.arrival_time.minute,
                        second=st.arrival_time.second,
                    )
                    return tmp_dt.timestamp() + delay
                return 0

            if arrival.time is not None:
                arrival.time = arrival.time - the_time
            elif arrival.delay is not None and stop_times_dataset is not None:
                arrival.time = (
                    _merge_today_with_stop_time(arrival, arrival.delay) - the_time
                )

            if arrival.departure_time is not None:
                arrival.departure_time = arrival.departure_time - the_time
            elif arrival.departure_delay is not None and stop_times_dataset is not None:
                arrival.departure_time = (
                    _merge_today_with_stop_time(arrival, arrival.delay) - the_time
                )

            return arrival

        return [_make_relative_arrival(copy(a)) for a in self.arrivals]
