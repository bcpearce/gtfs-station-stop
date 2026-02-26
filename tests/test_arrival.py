"""Test Arrival"""

from datetime import datetime

import pytest

from gtfs_station_stop.arrival import Arrival


def test_order_arrivals_by_soonest_time():
    a1 = Arrival(route="A1", trip="A1 Dest", time=1000)
    a2 = Arrival(route="A2", trip="A2 Dest", time=1200)
    a3 = Arrival(route="A3", trip="A3 Dest", time=1100)
    a4 = Arrival(route="A4", trip="A4 Dest", time=900)

    assert [a4, a1, a3, a2] == sorted([a1, a2, a3, a4])
    assert a1 > a4
    assert a1 == a1


def test_order_arrivals_by_soonest_departure_time():
    a1 = Arrival(route="A1", trip="A1 Dest", departure_time=1000)
    a2 = Arrival(route="A2", trip="A2 Dest", departure_time=1200)
    a3 = Arrival(route="A3", trip="A3 Dest", departure_time=1100)
    a4 = Arrival(route="A4", trip="A4 Dest", departure_time=900)
    a5 = Arrival(
        route="A5",
        trip="A5 Dest",
        departure_time=datetime(year=1970, month=1, day=1, hour=12),
    )
    assert [a4, a1, a3, a2, a5] == sorted([a1, a2, a3, a4, a5])


def test_invalid_comparisons():
    a1 = Arrival(route="A1", trip="A1 Dest")
    a2 = Arrival(route="A2", trip="A2 Dest")
    with pytest.raises(ValueError):
        assert a1 > a2
    with pytest.raises(ValueError):
        assert a1 == a2
    with pytest.raises(ValueError):
        assert a1 < a2

    a1.departure_time = 300
    a2.time = 100
    with pytest.raises(ValueError):
        assert a1 < a2
