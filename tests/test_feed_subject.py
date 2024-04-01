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
