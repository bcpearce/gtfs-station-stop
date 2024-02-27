import pathlib

import pytest

from gtfs_station_stop.trip_info import TripInfoDatabase

TEST_DIRECTORY = pathlib.Path(__file__).parent.resolve()


def test_invalid_gtfs_zip():
    with pytest.raises(RuntimeError):
        TripInfoDatabase(TEST_DIRECTORY / "data" / "gtfs_static_notrips.zip")


def test_get_trip_info_from_zip():
    ti = TripInfoDatabase(TEST_DIRECTORY / "data" / "gtfs_static.zip")
    assert ti["456_X..N04R"].service_id == "Weekday"
    assert ti["456_X..N04R"].shape_id == "X..N04R"
    assert ti["456_Y..N05R"].trip_headsign == "Northbound Y"


def test_get_close_match_trip_info_from_zip():
    ti = TripInfoDatabase(TEST_DIRECTORY / "data" / "gtfs_static.zip")
    assert ti.get_close_match("456_X..N").trip_headsign == "Northbound X"
    assert ti.get_close_match("321_Z..S").route_id == "Z"
