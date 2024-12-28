from gtfs_station_stop.route_info import RouteInfoDataset, RouteType


def test_invalid_gtfs_zip(test_directory):
    assert RouteInfoDataset() == RouteInfoDataset(
        test_directory / "data" / "gtfs_static_noroutes.zip"
    )


def test_get_route_info_from_zip(test_directory):
    rids = RouteInfoDataset(test_directory / "data" / "gtfs_static.zip")
    assert rids.route_infos["X"].long_name == "X Test Route"
    assert rids.route_infos["Y"].long_name == "Y Test Route"
    assert rids.route_infos["X"].color == "EE352E"
    assert rids.route_infos["X"].type == RouteType.SUBWAY


def test_route_info_has_pretty_name():
    assert RouteType.SUBWAY.pretty_name() == "Subway"


def test_route_info_pretty_name_fallback():
    assert RouteType.RAILWAY_SERVICE.pretty_name() == "RAILWAY_SERVICE"


def test_route_info_default_unknown():
    assert RouteType(-42) == RouteType.UNKNOWN
