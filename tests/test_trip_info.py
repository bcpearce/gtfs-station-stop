import pathlib

import pytest

from gtfs_station_stop.trip_info import TripInfoDatabase

TEST_DIRECTORY = pathlib.Path(__file__).parent.resolve()


def test_invalid_gtfs_zip():
    with pytest.raises(RuntimeError):
        TripInfoDatabase(TEST_DIRECTORY / "data" / "google_transit_notrips.zip")


def test_get_trip_info_from_zip():
    ti = TripInfoDatabase(TEST_DIRECTORY / "data" / "google_transit.zip")
    assert ti["BFA23GEN-B084-Weekday-00_090500_B..S46R"].service_id == "Weekday"
    assert ti["BFA23GEN-B084-Weekday-00_096850_B..N45R"].shape_id == "B..N45R"
    assert (
        ti["BFA23GEN-N098-Weekday-00_127700_N..N31R"].trip_headsign
        == "Astoria-Ditmars Blvd"
    )


def test_get_close_match_trip_info_from_zip():
    ti = TripInfoDatabase(TEST_DIRECTORY / "data" / "google_transit.zip")
    assert ti.get_close_match("114100_L..N").trip_headsign == "8 Av"
    assert ti.get_close_match("114100_L..N").route_id == "L"
