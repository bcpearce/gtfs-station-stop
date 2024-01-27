import pathlib

from gtfs_station_stop.feed_subject import FeedSubject

TEST_DIRECTORY = pathlib.Path(__file__).parent.resolve()


def test_init_FeedSubject():
    fs = FeedSubject("", set(["http://feed_1", "http://feed_2"]))
    assert len(fs.realtime_feed_uris) == 2
    fs = FeedSubject(
        "", ["http://feed_1", "http://feed_2", "http://feed_2", "http://feed_3"]
    )
    assert len(fs.realtime_feed_uris) == 3
