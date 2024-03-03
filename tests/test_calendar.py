import pathlib

import pytest
from fixtures import *  # noqa: F403

from gtfs_station_stop.calendar import Calendar

TEST_DIRECTORY = pathlib.Path(__file__).parent.resolve()


def test_invalid_gtfs_zip():
    with pytest.raises(RuntimeError):
        Calendar(TEST_DIRECTORY / "data" / "gtfs_static_nocalendar.zip")


def test_get_station_stop_info_from_zip():
    cal = Calendar(TEST_DIRECTORY / "data" / "gtfs_static.zip")
    assert cal["Regular"] is not None
