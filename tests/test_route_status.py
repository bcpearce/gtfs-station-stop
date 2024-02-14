import pytest
from fixtures import *

from gtfs_station_stop.feed_subject import FeedSubject
from gtfs_station_stop.route_status import RouteStatus


def test_create_route_status():
    rs = RouteStatus("C", FeedSubject("", []))
    assert hasattr(rs, "alerts")


def test_subscribe_to_feed(feed_subject):
    rs = RouteStatus("C", feed_subject)
    assert len(feed_subject.subscribers) == 1
    del rs


@pytest.mark.skip(reason="mock data must be tailored better and time.time mocked out")
def test_update_feed(feed_subject):
    rs = RouteStatus("C", feed_subject)
    assert rs.last_updated is None
    feed_subject.update()
    print("Detected Alerts:")
    for arr in rs.alerts:
        print(arr)
    assert len(rs.alerts) > 0
    assert rs.last_updated is not None
