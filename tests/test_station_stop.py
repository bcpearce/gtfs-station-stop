import glob
import os
import pathlib
from unittest.mock import MagicMock

import dotenv
import pytest
import pytest_httpserver

from gtfs_station_stop.feed_subject import FeedSubject
from gtfs_station_stop.station_stop import StationStop


@pytest.fixture(scope="session")
def mock_feed_server():
    TEST_DIRECTORY = pathlib.Path(__file__).parent.resolve()
    MOCK_DATA_MAP = dict(
        (f"/{path.name}", path.read_bytes())
        for path in (
            pathlib.Path(x) for x in glob.glob(str(TEST_DIRECTORY / "data" / "*.dat"))
        )
    )
    print("creating test server")
    server = pytest_httpserver.HTTPServer()
    server.start()
    # Install the reuquests that point to files
    server.urls = []
    for endpoint, data in MOCK_DATA_MAP.items():
        server.expect_request(endpoint).respond_with_data(data)
        server.urls.append(server.url_for(endpoint))

    yield server

    server.clear()
    if server.is_running():
        server.stop()

    server.check_assertions()
    server.clear()


@pytest.fixture
def mock_feed_subject(mock_feed_server):
    return FeedSubject("", mock_feed_server.urls)


@pytest.fixture
def nyct_feed_subject():
    feed_urls = [
        "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-bdfm",
        "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-g",
        "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-jz",
        "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-nqrw",
        "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-l",
        "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs",
        "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/camsys%2Fsubway-alerts",
    ]
    dotenv.load_dotenv()
    return FeedSubject(os.environ.get("API_KEY"), feed_urls)


@pytest.fixture
def feed_subject(mock_feed_subject, nyct_feed_subject):
    # Set the feed server to use either mock data read from the tests/data directory, or to use real data
    # By default, use mock data
    feed_dict = {"MOCK": mock_feed_subject, "NYCT": nyct_feed_subject}
    feed_key = os.environ.get("GTFS_SOURCE", "MOCK")
    print(f"Using feed subject {feed_key}")
    return feed_dict.get(feed_key)


def test_create_station_stop():
    ss = StationStop("L20N", FeedSubject("", []))
    assert hasattr(ss, "alerts")
    assert hasattr(ss, "arrivals")


def test_subscribe_to_feed(feed_subject):
    ss = StationStop("L20N", feed_subject)
    assert len(feed_subject.subscribers) == 1
    del ss


def test_update_feed(feed_subject):
    ss = StationStop("L20N", feed_subject)
    assert ss.last_updated is None
    feed_subject.update()
    print("Detected Arrivals:")
    for arr in ss.arrivals:
        print(arr)
    assert len(ss.arrivals) > 0
    assert ss.last_updated is not None


def test_multiple_subscribers(feed_subject):
    ss1 = StationStop("L20N", feed_subject)
    ss2 = StationStop("L20S", feed_subject)
    assert ss1.last_updated is None
    assert ss2.last_updated is None
    feed_subject.unsubscribe(ss2)
    feed_subject.update()
    assert ss1.last_updated is not None
    assert ss2.last_updated is None
    assert len(ss1.arrivals) > 0
    assert len(ss2.arrivals) == 0
