from gtfs_station_stop.feed_subject import FeedSubject
from gtfs_station_stop.route_status import RouteStatus


def test_create_route_status():
    rs = RouteStatus("Z", FeedSubject([]))
    assert hasattr(rs, "alerts")


def test_subscribe_to_feed(feed_subject):
    rs = RouteStatus("Z", feed_subject)
    assert len(feed_subject.subscribers) == 1
    del rs


def test_update_feed(feed_subject):
    rs = RouteStatus("Z", feed_subject)
    assert rs.last_updated is None
    feed_subject.update()
    assert len(rs.alerts) == 1
    assert rs.last_updated is not None
