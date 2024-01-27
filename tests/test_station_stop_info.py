import pathlib

import pytest

from gtfs_station_stop.station_stop_info import StationStopInfoDatabase

TEST_DIRECTORY = pathlib.Path(__file__).parent.resolve()


def test_invalid_gtfs_zip():
    with pytest.raises(RuntimeError):
        StationStopInfoDatabase(TEST_DIRECTORY / "data" / "google_transit_nostops.zip")


def test_get_station_stop_info_from_zip():
    ssi = StationStopInfoDatabase(TEST_DIRECTORY / "data" / "google_transit.zip")
    assert ssi["101"].name == "Van Cortlandt Park-242 St"
    assert ssi["107"].name == "215 St"
    assert ssi["107N"].parent == ssi["107"]
