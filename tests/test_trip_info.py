import pathlib

from gtfs_station_stop.static_dataset import async_factory
from gtfs_station_stop.trip_info import TripInfoDataset

TEST_DIRECTORY = pathlib.Path(__file__).parent.resolve()


def test_invalid_gtfs_zip():
    assert TripInfoDataset() == TripInfoDataset(
        TEST_DIRECTORY / "data" / "gtfs_static_notrips.zip"
    )


def test_get_trip_info_from_zip(good_trip_info_dataset):
    assert good_trip_info_dataset["456_X..N04R"].service_id == "Weekday"
    assert good_trip_info_dataset["456_X..N04R"].shape_id == "X..N04R"
    assert good_trip_info_dataset["456_Y..N05R"].trip_headsign == "Northbound Y"


def test_get_close_match_trip_info_from_zip(good_trip_info_dataset):
    assert (
        good_trip_info_dataset.get_close_match("456_X..N").trip_headsign
        == "Northbound X"
    )
    assert good_trip_info_dataset.get_close_match("321_Z..S").route_id == "Z"


def test_get_close_match_trip_with_service_id_from_zip(good_trip_info_dataset):
    assert good_trip_info_dataset.get_close_match("456_X..N", "Special") is None
    assert good_trip_info_dataset.get_close_match("456_X..N", "Weekday") is not None


def test_concatenated_trip_info_from_zips():
    gtfs_static_zips = [
        TEST_DIRECTORY / "data" / "gtfs_static.zip",
        TEST_DIRECTORY / "data" / "gtfs_static_supl.zip",
    ]
    ti = TripInfoDataset(*gtfs_static_zips)
    assert ti.get_close_match("456_X..N").trip_headsign == "Northbound X"
    assert ti.get_close_match("987_X..S21R").trip_headsign == "Southbound Special X"


def test_get_trip_info_from_url(mock_feed_server):
    ti = TripInfoDataset(
        *[
            url
            for url in mock_feed_server.static_urls
            if url.endswith("gtfs_static.zip")
        ]
    )
    assert ti["456_X..N04R"].service_id == "Weekday"
    assert ti["456_X..N04R"].shape_id == "X..N04R"
    assert ti["456_Y..N05R"].trip_headsign == "Northbound Y"


def test_get_route_ids(good_trip_info_dataset):
    ti = good_trip_info_dataset
    assert set(ti.get_route_ids()) == set(["X", "Y", "Z"])


async def test_async_trip_info_merge_existing(mock_feed_server):
    ti: TripInfoDataset = await async_factory(
        TripInfoDataset,
        *[
            url
            for url in mock_feed_server.static_urls
            if url.endswith("gtfs_static.zip")
        ],
        headers={"api-key": "TEST_KEY"},
    )
    assert ti.get_close_match("456_X..N") is not None
    assert ti.get_close_match("987_X..N21R") is None

    ti = await async_factory(
        ti,
        *[
            url
            for url in mock_feed_server.static_urls
            if url.endswith("gtfs_static_supl.zip")
        ],
        headers={"api-key": "TEST_KEY"},
    )

    assert ti.get_close_match("456_X..N") is not None
    assert ti.get_close_match("987_X..N21R") is not None
