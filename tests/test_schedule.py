from dataclasses import asdict

from gtfs_station_stop.schedule import GtfsSchedule, async_build_schedule


async def test_async_build_schedule(mock_feed_server, snapshot):
    schedule: GtfsSchedule = await async_build_schedule(
        *[
            url
            for url in mock_feed_server.static_urls
            if url.endswith("gtfs_static.zip")
        ]
    )
    assert snapshot == asdict(schedule)


async def test_async_build_schedule_add_data_later(mock_feed_server, snapshot):
    schedule: GtfsSchedule = await async_build_schedule(
        *[
            url
            for url in mock_feed_server.static_urls
            if url.endswith("gtfs_static.zip")
        ]
    )
    orig_data = asdict(schedule)

    await schedule.async_update_schedule(
        *[
            url
            for url in mock_feed_server.static_urls
            if url.endswith("gtfs_static_supl.zip")
        ]
    )
    assert orig_data != asdict(schedule)
    assert snapshot == asdict(schedule)
