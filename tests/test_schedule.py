"""Test Schedule."""

from dataclasses import asdict
from datetime import datetime

import syrupy.filters
from aiohttp import ClientSession

from gtfs_station_stop.route_info import RouteInfoDataset
from gtfs_station_stop.schedule import (
    GtfsSchedule,
    async_build_schedule,
)
from gtfs_station_stop.stop_times import StopTimesDataset

schedule_filter = syrupy.filters.props("tmp_dir", "tmp_dir_path", "resources")


async def test_async_build_schedule(mock_feed_server, snapshot):
    async with ClientSession() as session:
        schedule: GtfsSchedule = await async_build_schedule(
            *[
                url
                for url in mock_feed_server.static_urls
                if url.endswith("gtfs_static.zip")
            ],
            session=session,
        )
    assert snapshot(exclude=schedule_filter) == asdict(schedule)
    assert isinstance(schedule.stop_times_ds, StopTimesDataset)

    assert schedule.get_route_color("X") == "EE352E"
    assert schedule.get_route_text_color("Y") == "FFFFFF"
    assert schedule.get_trip_headsign("123_X..N01R") == "Northbound X"
    assert schedule.get_route_type("X") == "Subway"
    assert schedule.get_stop_info("101S").parent.id == "101"
    assert schedule.get_stop_info("101S").name == "Test Station Main St"


async def test_async_build_schedule_add_data_later(mock_feed_server, snapshot):
    schedule: GtfsSchedule = await async_build_schedule(
        *[
            url
            for url in mock_feed_server.static_urls
            if url.endswith("gtfs_static.zip")
        ]
    )
    orig_data = asdict(schedule)

    await schedule.async_build_schedule(
        *[
            url
            for url in mock_feed_server.static_urls
            if url.endswith("gtfs_static_supl.zip")
        ]
    )
    await schedule.async_load_stop_times()

    assert orig_data != asdict(schedule)
    assert snapshot(exclude=schedule_filter) == asdict(schedule)
    assert isinstance(schedule.stop_times_ds, StopTimesDataset)
    assert isinstance(schedule.route_info_ds, RouteInfoDataset)


async def test_stop_time_filtering(mock_feed_server, snapshot):
    schedule: GtfsSchedule = await async_build_schedule(
        *[
            url
            for url in mock_feed_server.static_urls
            if url.endswith("gtfs_static.zip")
        ]
    )
    await schedule.async_load_stop_times({"101N"})

    assert snapshot(
        exclude=syrupy.filters.props("tmp_dir", "tmp_dir_path", "resources")
    ) == asdict(schedule)

    assert schedule.stop_times_ds.get("STOP_TIME_TRIP", 1) is not None


async def test_scheduled_arrival(mock_feed_server):
    schedule: GtfsSchedule = await async_build_schedule(
        *[
            url
            for url in mock_feed_server.static_urls
            if url.endswith("gtfs_static.zip")
        ]
    )
    await schedule.async_load_stop_times(
        set(schedule.station_stop_info_ds.station_stop_infos.keys())
    )

    arrivals = schedule.get_arrivals_between_times(
        "102S",
        datetime(year=2024, month=1, day=1, hour=0),
        datetime(year=2024, month=1, day=1, hour=1),
    )
    assert len(arrivals) == 3

    arrivals = schedule.get_arrivals_between_times(
        "102S",
        datetime(year=2024, month=1, day=1, hour=0, minute=0),
        datetime(year=2024, month=1, day=1, hour=0, minute=25),
    )
    assert len(arrivals) == 2
