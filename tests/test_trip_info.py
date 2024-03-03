import pathlib

import pytest
from fixtures import *  # noqa: F403

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


def test_concatenated_trip_info_from_zips():
    gtfs_static_zips = [
        TEST_DIRECTORY / "data" / "gtfs_static.zip",
        TEST_DIRECTORY / "data" / "gtfs_static_supl.zip",
    ]
    ti = TripInfoDatabase(gtfs_static_zips)
    assert ti.get_close_match("456_X..N").trip_headsign == "Northbound X"
    assert ti.get_close_match("987_X..S21R").trip_headsign == "Southbound Special X"


def test_get_trip_info_from_url(mock_feed_server):
    ti = TripInfoDatabase(
        [url for url in mock_feed_server.static_urls if url.endswith("gtfs_static.zip")]
    )
    assert ti["456_X..N04R"].service_id == "Weekday"
    assert ti["456_X..N04R"].shape_id == "X..N04R"
    assert ti["456_Y..N05R"].trip_headsign == "Northbound Y"
