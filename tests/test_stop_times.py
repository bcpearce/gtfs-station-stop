"""Test Stop Times"""

import datetime
import pathlib
import time

from freezegun import freeze_time

from gtfs_station_stop.arrival import Arrival
from gtfs_station_stop.station_stop import StationStop
from gtfs_station_stop.stop_times import GtfsArrivalDepartureTime

TEST_DIRECTORY = pathlib.Path(__file__).parent.resolve()


def test_gtfs_arrival_departure_time():
    time1 = GtfsArrivalDepartureTime.strptime("24:00:00")
    assert (time1.hour, time1.minute, time1.second) == (24, 0, 0)
    time1 = GtfsArrivalDepartureTime.strptime("11:59:11")
    assert (time1.hour, time1.minute, time1.second) == (11, 59, 11)
    time1 = GtfsArrivalDepartureTime.strptime("08:00:01")
    assert (time1.hour, time1.minute, time1.second) == (8, 0, 1)


def test_stop_times_from_zip(stop_times_dataset):
    assert stop_times_dataset.get("STOP_TIME_TRIP", 1).stop_id == "101N"
    assert stop_times_dataset.get("STOP_TIME_TRIP", 2).stop_id == "102N"
    assert stop_times_dataset.get("STOP_TIME_TRIP", 3).stop_id == "103N"
    assert stop_times_dataset.get("654_Y..S05R", 1) is None


@freeze_time(datetime.datetime.fromtimestamp(5 * 60 * 60, tz=datetime.UTC))
def test_stop_times_merged_with_realtime_arrival(feed_subject, stop_times_dataset):
    arrival_1 = Arrival(route="A", trip="STOP_TIME_TRIP", delay=-1200, stop_sequence=1)
    arrival_2 = Arrival(route="A", trip="STOP_TIME_TRIP", delay=300, stop_sequence=2)

    station_stop_1 = StationStop("101N", feed_subject)
    station_stop_2 = StationStop("102N", feed_subject)

    station_stop_1.arrivals.append(arrival_1)
    station_stop_2.arrivals.append(arrival_2)

    times = [
        ss.get_time_to_arrivals(time.time(), stop_times_dataset=stop_times_dataset)[
            0
        ].time
        for ss in [station_stop_1, station_stop_2]
    ]

    assert times == [8 * 60, 35 * 60]
