import math

from gtfs_station_stop.feed_subject import FeedSubject


def test_init_FeedSubject():
    fs = FeedSubject(set(["http://feed_1", "http://feed_2"]))
    assert len(fs.realtime_feed_uris) == 2
    fs = FeedSubject(
        ["http://feed_1", "http://feed_2", "http://feed_2", "http://feed_3"]
    )
    assert len(fs.realtime_feed_uris) == 3


def test_FeedSubject_update_does_not_throw_with_zero_uris():
    fs = FeedSubject([])
    fs.update()


def test_rate_limiting():
    fs = FeedSubject([])
    fs.delay_between_api_calls = 0.5
    assert math.isclose(fs.max_api_calls_per_second, 2, abs_tol=0.0001)

    fs.max_api_calls_per_second = 3
    assert math.isclose(fs.delay_between_api_calls, 0.33333, abs_tol=0.0001)

    fs.max_api_calls_per_second = None
    assert fs.delay_between_api_calls is None
