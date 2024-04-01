import pytest

from gtfs_station_stop.route_info import RouteInfoDatabase


def test_invalid_gtfs_zip(test_directory):
    with pytest.raises(RuntimeError):
        RouteInfoDatabase(test_directory / "data" / "gtfs_static_noroutes.zip")


def test_get_route_info_from_zip(test_directory):
    ri_db = RouteInfoDatabase(test_directory / "data" / "gtfs_static.zip")
    assert ri_db.route_infos["X"].long_name == "X Test Route"
    assert ri_db.route_infos["Y"].long_name == "Y Test Route"
