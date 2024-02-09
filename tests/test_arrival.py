from gtfs_station_stop.arrival import Arrival


def test_order_arrivals_by_soonest_time():
    a1 = Arrival(1000, "A1", "A1 Dest")
    a2 = Arrival(1200, "A2", "A2 Dest")
    a3 = Arrival(1100, "A3", "A3 Dest")
    a4 = Arrival(900, "A4", "A4 Dest")

    assert [a4, a1, a3, a2] == sorted([a1, a2, a3, a4])
