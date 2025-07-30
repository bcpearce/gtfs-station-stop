"""Test Stop Times"""

import pathlib

TEST_DIRECTORY = pathlib.Path(__file__).parent.resolve()


def test_stop_times_from_zip(stop_times_dataset):
    assert stop_times_dataset.get("STOP_TIME_TRIP", 1).stop_id == "101N"
    assert stop_times_dataset.get("STOP_TIME_TRIP", 2).stop_id == "102N"
    assert stop_times_dataset.get("STOP_TIME_TRIP", 3).stop_id == "103N"
    assert stop_times_dataset.get("654_Y..S05R", 1) is None
