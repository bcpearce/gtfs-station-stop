import pathlib

import pytest
from fixtures import *  # noqa: F403

from gtfs_station_stop.station_stop_info import StationStopInfoDatabase

TEST_DIRECTORY = pathlib.Path(__file__).parent.resolve()


def test_invalid_gtfs_zip():
    with pytest.raises(RuntimeError):
        StationStopInfoDatabase(TEST_DIRECTORY / "data" / "gtfs_static_nostops.zip")


def test_get_station_stop_info_from_zip():
    ssi = StationStopInfoDatabase(TEST_DIRECTORY / "data" / "gtfs_static.zip")
    assert ssi["101"].name == "Test Station Main St"
    assert ssi["101N"].name == "Test Station Main St"
    assert ssi["102S"].parent == ssi["102"]


def test_conatenated_station_stop_info_from_zip():
    gtfs_static_zips = [
        TEST_DIRECTORY / "data" / "gtfs_static.zip",
        TEST_DIRECTORY / "data" / "gtfs_static_supl.zip",
    ]
    ssi = StationStopInfoDatabase(gtfs_static_zips)
    assert ssi["101"].name == "Test Station Main St"
    assert ssi["201"].name == "Test Station Last St"


def test_get_station_stop_info_from_url(mock_feed_server):
    ssi = StationStopInfoDatabase(
        [url for url in mock_feed_server.static_urls if url.endswith("gtfs_static.zip")]
    )
    assert ssi["101"].name == "Test Station Main St"
    assert ssi["101N"].name == "Test Station Main St"
    assert ssi["102S"].parent == ssi["102"]
