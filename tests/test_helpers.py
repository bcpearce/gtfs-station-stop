import datetime

import pytest
from google.transit.gtfs_realtime_pb2 import FeedEntity, TimeRange

from gtfs_station_stop import helpers


@pytest.fixture
def active_period_feed_entity():
    # TODO update feed entity to insert time range intervals
    fe = FeedEntity()
    fe.active_period = [
        TimeRange(start=100, end=120),
        TimeRange(start=150, end=200),
        TimeRange(start=400),
        TimeRange(end=50),
    ]


@pytest.mark.skip(reason="fixture must be set up")
def test_return_none_if_not_active(active_period_feed_entity):
    assert helpers.is_none_or_ends_at(active_period_feed_entity, 130) is None
    assert helpers.is_none_or_ends_at(active_period_feed_entity, 60) is None


@pytest.mark.skip(reason="fixture mest be set up")
def test_return_end_if_active(active_period_feed_entity):
    assert helpers.is_none_or_ends_at(
        active_period_feed_entity, 110
    ) == datetime.datetime.fromtimestamp(120)
    assert helpers.is_none_or_ends_at(
        active_period_feed_entity, 160
    ) == datetime.datetime.fromtimestamp(200)
    assert (
        helpers.is_none_or_ends_at(active_period_feed_entity, 500)
        == datetime.datetime.max
    )
    assert (
        helpers.is_none_or_ends_at(active_period_feed_entity, 20)
        == datetime.datetime.fromtimestamp
    )
