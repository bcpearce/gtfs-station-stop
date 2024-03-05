from gtfs_station_stop.feed_subject import FeedSubject
from gtfs_station_stop.station_stop import StationStop


def test_create_station_stop():
    ss = StationStop("L20N", FeedSubject("", []))
    assert hasattr(ss, "alerts")
    assert hasattr(ss, "arrivals")


def test_subscribe_to_feed(feed_subject):
    ss = StationStop("L20N", feed_subject)
    assert len(feed_subject.subscribers) == 1
    del ss


def test_update_feed(feed_subject):
    ss = StationStop("101N", feed_subject)
    assert ss.last_updated is None
    feed_subject.update()
    print("Detected Arrivals:")
    for arr in ss.arrivals:
        print(arr)
    assert len(ss.arrivals) == 2
    assert ss.last_updated is not None
    arrival_routes = [a.route for a in ss.arrivals]
    assert "X" in arrival_routes
    assert "Y" in arrival_routes


def test_multiple_subscribers(feed_subject):
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
