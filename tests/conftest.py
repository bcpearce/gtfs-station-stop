from pathlib import Path
from zipfile import ZipFile

from google.transit import gtfs_realtime_pb2


# Prepare the raw files into a zip archives for use with the library.
def create_static_data():
    with ZipFile(Path("tests/data/gtfs_static_nostops.zip"), "w") as zp:
        for gtfs_file in Path.iterdir(Path("tests/data/gtfs_static")):
            if gtfs_file.name != "stops.txt":
                zp.write(gtfs_file, gtfs_file.name)

    with ZipFile(Path("tests/data/gtfs_static_notrips.zip"), "w") as zp:
        for gtfs_file in Path.iterdir(Path("tests/data/gtfs_static")):
            if gtfs_file.name != "trips.txt":
                zp.write(gtfs_file, gtfs_file.name)

    with ZipFile(Path("tests/data/gtfs_static.zip"), "w") as zp:
        for gtfs_file in Path.iterdir(Path("tests/data/gtfs_static")):
            zp.write(gtfs_file, gtfs_file.name)


def create_realtime_data():
    feed = gtfs_realtime_pb2.FeedMessage()

    feed.header.gtfs_realtime_version = "2.0"

    entities = [feed.entity.add() for _ in range(5)]

    elem = entities[0]
    elem.id = "1"
    elem.trip_update.trip.route_id = "X"
    for t, s in zip([30, 45], ["102N", "103N"]):
        stu = elem.trip_update.stop_time_update.add()
        stu.arrival.time = t
        stu.stop_id = s

    elem = entities[1]
    elem.id = "2"
    elem.trip_update.trip.route_id = "Y"
    for t, s in zip([35, 51, 68], ["101N", "102N", "103N"]):
        stu = elem.trip_update.stop_time_update.add()
        stu.arrival.time = t
        stu.stop_id = s

    elem = entities[2]
    elem.id = "3"
    elem.trip_update.trip.route_id = "Z"
    for t, s in zip([10, 0, 8], ["103S", "102S", "101S"]):
        stu = elem.trip_update.stop_time_update.add()
        stu.arrival.time = t
        stu.stop_id = s

    elem = entities[3]
    elem.id = "4"
    elem.trip_update.trip.route_id = "X"
    for t, s in zip([31, 50, 60], ["101N", "102N", "103N"]):
        stu = elem.trip_update.stop_time_update.add()
        stu.arrival.time = t
        stu.stop_id = s

    elem = entities[4]
    elem.id = "Z Alert"
    ie = elem.alert.informed_entity.add()
    ie.route_id = "Z"
    ap = elem.alert.active_period.add()
    ap.start = 1
    hd0 = elem.alert.header_text.translation.add()
    hd0.text = "Southbound Z is not ok."
    hd0.language = "en"

    print("Using Realtime Feed Stop Time Updates:")
    print(feed)

    with open("tests/data/realtime.dat", "wb") as fd:
        fd.write(feed.SerializeToString())


create_static_data()
create_realtime_data()
