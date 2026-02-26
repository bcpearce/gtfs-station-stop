"""Tests for informing the station_stop class of GTFS Realtime updates."""

import asyncio
import datetime
import math
import time

import pytest
from freezegun import freeze_time

from gtfs_station_stop.feed_subject import FeedSubject
from gtfs_station_stop.route_status import RouteStatus
from gtfs_station_stop.station_stop import StationStop
from gtfs_station_stop.vehicle import Vehicle


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
    assert len(ss.arrivals) == 3
    assert ss.last_updated == time.time()
    arrival_routes = [a.route for a in ss.arrivals]
    assert "X" in arrival_routes
    assert "Y" in arrival_routes
    for arrival in ss.arrivals:
        assert arrival.destination == "103N"


@freeze_time(datetime.datetime.now())
async def test_async_update_feed(feed_subject: FeedSubject):
    """Asynchronous version of update."""
    ss = StationStop("101N", feed_subject)
    rs = RouteStatus("101N", feed_subject)
    assert ss.last_updated is None
    await feed_subject.async_update()
    assert len(ss.arrivals) == 3
    assert ss.last_updated == time.time()
    assert rs.last_updated == time.time()
    arrival_routes = [a.route for a in ss.arrivals]
    assert "X" in arrival_routes
    assert "Y" in arrival_routes
    assert "A" in arrival_routes


def test_multiple_subscribers(feed_subject: FeedSubject):
    ss1 = StationStop("103N", feed_subject)
    ss2 = StationStop("103S", feed_subject)
    assert ss1.last_updated is None
    assert ss2.last_updated is None
    feed_subject.unsubscribe(ss2)
    feed_subject.update()
    assert ss1.last_updated is not None
    assert ss2.last_updated is None
    assert len(ss1.arrivals) == 4
    assert len(ss2.arrivals) == 0


@pytest.mark.skip
async def test_rate_limit(feed_subject: FeedSubject):
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


@freeze_time(datetime.datetime.now())
@pytest.mark.parametrize(
    "trip_id,latitude,longitude,bearing",
    [("1", 40.8, -73.9, 10.0), ("2", 42.0, -71.0, 20.0)],
)
async def test_map_vehicle_positions(
    feed_subject: FeedSubject, trip_id, latitude, longitude, bearing
) -> None:
    """Test mapping vehicle positions to an arrival."""
    ss1 = StationStop("101N", feed_subject)
    ss2 = StationStop("102N", feed_subject)
    ss3 = StationStop("103N", feed_subject)
    await feed_subject.async_update()
    arrivals = ss1.arrivals + ss2.arrivals + ss3.arrivals
    for arrival in arrivals:
        if arrival.trip == trip_id:
            assert isinstance(arrival.vehicle, Vehicle)
            assert arrival.vehicle.trip_id == trip_id
            assert arrival.vehicle.latitude is not None
            assert arrival.vehicle.longitude is not None
            assert arrival.vehicle.bearing is not None

            assert math.isclose(arrival.vehicle.latitude, latitude, abs_tol=0.01)
            assert math.isclose(arrival.vehicle.longitude, longitude, abs_tol=0.01)
            assert math.isclose(arrival.vehicle.bearing, bearing, abs_tol=0.01)
