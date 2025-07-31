import glob
import os
import pathlib
from collections.abc import Container

import pytest_httpserver
import yarl


class TestServer(pytest_httpserver.HTTPServer):
    """Test Server with the list of URLS"""

    static_urls: Container[yarl.URL]
    realtime_urls: Container[yarl.URL]

    def __init__(self) -> None:
        super().__init__()
        self.static_urls = []
        self.realtime_urls = []


def create_mock_feed_server(data_directory: os.PathLike) -> TestServer:
    """Creates a Mock Feed using local files."""
    server = TestServer()
    server.start()

    # Install the requests that point to realtime files
    MOCK_REALTIME_DATA_MAP = dict(
        (f"/{path.name}", path.read_bytes())
        for path in (
            pathlib.Path(x)
            for x in glob.glob(str(pathlib.Path(data_directory) / "*.pb"))
        )
    )
    server.realtime_urls = []
    for endpoint, data in MOCK_REALTIME_DATA_MAP.items():
        server.expect_request(endpoint).respond_with_data(data)
        server.realtime_urls.append(server.url_for(endpoint))

    # Install the requests that point to static files
    MOCK_STATIC_DATA_MAP = dict(
        (f"/{path.name}", path.read_bytes())
        for path in (
            pathlib.Path(x)
            for x in glob.glob(str(pathlib.Path(data_directory) / "*.zip"))
        )
    )
    server.static_urls = []
    for endpoint, data in MOCK_STATIC_DATA_MAP.items():
        server.expect_request(endpoint).respond_with_data(data)
        server.static_urls.append(server.url_for(endpoint))

    return server
