#!/usr/bin/python
import argparse
import os

import dotenv

import gtfs_station_stop.__about__
from gtfs_station_stop.feed_subject import FeedSubject
from gtfs_station_stop.route_status import RouteStatus
from gtfs_station_stop.station_stop import StationStop
from gtfs_station_stop.station_stop_info import (  # noqa: F401
    StationStopInfo,
    StationStopInfoDatabase,
)
from gtfs_station_stop.trip_info import TripInfo, TripInfoDatabase  # noqa: F401

dotenv.load_dotenv()

parser = argparse.ArgumentParser(
    prog="GTFS Station Stop", description="Use for static and realtime GTFS info"
)

parser.add_argument(
    "-v", "--version", action="store_true", help="display the module version"
)
parser.add_argument("-i", "--info-zip", help="input GTFS zip file path of static data")
parser.add_argument("-k", "--api-key", help="API key for feed URLs")
parser.add_argument("-u", "--feed-urls", help="feed URL list", nargs="*")
parser.add_argument(
    "-s", "--stops", help="list of stops to check for arrivals and alerts", nargs="*"
)
parser.add_argument(
    "-r", "--routes", help="list of routes to check for alerts", nargs="*"
)
parser.add_argument(
    "--lang", type=str, default="en", help="language to read alerts", nargs="?"
)

args = parser.parse_args()

if args.version:
    print(gtfs_station_stop.__about__.__version__)
    exit(0)

# Get the API Key, argument takes precedent of environment variable
api_key = args.api_key or os.environ.get("API_KEY")

ssi_db = StationStopInfoDatabase(args.info_zip) if args.info_zip is not None else None
ti_db = TripInfoDatabase(args.info_zip) if args.info_zip is not None else None

feed_subject = (
    FeedSubject(api_key, args.feed_urls) if args.feed_urls is not None else None
)
station_stops = [StationStop(id, feed_subject) for id in args.stops]
route_statuses = [RouteStatus(id, feed_subject) for id in args.routes]
feed_subject.update()

for stop in station_stops:
    if ssi_db is not None:
        print(ssi_db[stop.id])
        print(
            [
                [arrival.route, arrival.time, ti_db.get_close_match(arrival.trip)]
                for arrival in sorted(stop.get_time_to_arrivals())
            ]
        )
        print(stop.alerts)

for route in route_statuses:
    for alert in route.alerts:
        print(f"Alert! {route.id}")
        print(alert.header_text.get(args.lang))
        print(alert.description_text.get(args.lang))
        print()
        print()
