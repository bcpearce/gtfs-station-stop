import glob
import os
import pathlib

import pytest_httpserver


def create_mock_feed_server(data_directory: os.PathLike):
    MOCK_DATA_MAP = dict(
        (f"/{path.name}", path.read_bytes())
        for path in (
            pathlib.Path(x)
            for x in glob.glob(str(pathlib.Path(data_directory) / "*.dat"))
        )
    )
    server = pytest_httpserver.HTTPServer()
    server.start()
    # Install the requests that point to files
    server.urls = []
    for endpoint, data in MOCK_DATA_MAP.items():
        server.expect_request(endpoint).respond_with_data(data)
        server.urls.append(server.url_for(endpoint))

    return server
