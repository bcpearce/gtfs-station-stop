"""Tests for informing the station_stop class of GTFS Realtime updates."""

import asyncio
import datetime
import time

import pytest
from freezegun import freeze_time

from gtfs_station_stop.feed_subject import FeedSubject
from gtfs_station_stop.station_stop import StationStop


def test_create_station_stop():
    ss = StationStop("L20N", FeedSubject([]))
    assert hasattr(ss, "alerts")
    assert hasattr(ss, "arrivals")


def test_subscribe_to_feed(feed_subject: FeedSubject):
    ss = StationStop("L20N", feed_subject)
    assert len(feed_subject.subscribers) == 1
    del ss


@freeze_time(datetime.datetime.now())
def test_update_feed(feed_subject: FeedSubject):
    ss = StationStop("101N", feed_subject)
    assert ss.last_updated is None
    feed_subject.update()
    assert len(ss.arrivals) == 2
    assert ss.last_updated == time.time()
    arrival_routes = [a.route for a in ss.arrivals]
    assert "X" in arrival_routes
    assert "Y" in arrival_routes


@freeze_time(datetime.datetime.now())
async def test_async_update_feed(feed_subject: FeedSubject):
    """Asynchronous version of update."""
    ss = StationStop("101N", feed_subject)
    assert ss.last_updated is None
    await feed_subject.async_update()
    assert len(ss.arrivals) == 2
    assert ss.last_updated == time.time()
    arrival_routes = [a.route for a in ss.arrivals]
    assert "X" in arrival_routes
    assert "Y" in arrival_routes


def test_multiple_subscribers(feed_subject: FeedSubject):
    ss1 = StationStop("103N", feed_subject)
    ss2 = StationStop("103S", feed_subject)
    assert ss1.last_updated is None
    assert ss2.last_updated is None
    feed_subject.unsubscribe(ss2)
    feed_subject.update()
    assert ss1.last_updated is not None
    assert ss2.last_updated is None
    assert len(ss1.arrivals) == 3
    assert len(ss2.arrivals) == 0


async def async_test_rate_limit(feed_subject: FeedSubject):
    StationStop("101N", feed_subject)
    feed_subject.max_api_calls_per_second = 1

    # test timeout case
    with freeze_time(datetime.datetime.now()) as freezer, pytest.raises(TimeoutError):
        async with asyncio.timeout(0.5):
            freezer.tick()  # enough to timeout, not enough to get past rate limiting
            await feed_subject.async_update()

    # test non-timeout case
    with freeze_time(datetime.datetime.now()) as freezer:
        async with asyncio.timeout(2.0):
            freezer.tick()
            await feed_subject.async_update()
