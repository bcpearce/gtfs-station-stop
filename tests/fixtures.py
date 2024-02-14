import os
import pathlib

import dotenv
import pytest
from mock_feed_server import create_mock_feed_server

from gtfs_station_stop.feed_subject import FeedSubject


@pytest.fixture(scope="session")
def mock_feed_server():
    TEST_DIRECTORY = pathlib.Path(__file__).parent.resolve()
    server = create_mock_feed_server(TEST_DIRECTORY / "data")

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