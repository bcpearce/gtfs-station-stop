import datetime

import pytest
from google.transit.gtfs_realtime_pb2 import FeedEntity

from gtfs_station_stop import helpers


@pytest.fixture
def active_period_alert():
    # TODO update feed entity to insert time range intervals
    fe = FeedEntity()

    ap = fe.alert.active_period.add()
    ap.start = 100
    ap.end = 120

    ap = fe.alert.active_period.add()
    ap.start = 150
    ap.end = 200

    ap = fe.alert.active_period.add()
    ap.start = 400

    ap = fe.alert.active_period.add()
    ap.end = 50
    return fe.alert


def test_return_none_if_not_active(active_period_alert):
    assert helpers.is_none_or_ends_at(active_period_alert, 130.0) is None
    assert helpers.is_none_or_ends_at(active_period_alert, 60.0) is None


def test_return_end_if_active(active_period_alert):
    assert helpers.is_none_or_ends_at(
        active_period_alert, 110.0
    ) == datetime.datetime.fromtimestamp(120)
    assert helpers.is_none_or_ends_at(
        active_period_alert, 160.0
    ) == datetime.datetime.fromtimestamp(200)
    assert (
        helpers.is_none_or_ends_at(active_period_alert, 500.0) == datetime.datetime.max
    )
    assert helpers.is_none_or_ends_at(
        active_period_alert, 20.0
    ) == datetime.datetime.fromtimestamp(50)


async def test_nested_gtfs_zip(test_directory):
    nested = await helpers.unpack_nested_zips(
        test_directory / "data" / "gtfs_nested.zip"
    )
    assert len(nested) == 2
