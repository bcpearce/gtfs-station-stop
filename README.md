# GTFS Station Stop

A project for organizing GTFS Real-Time data for use as a homeassistant sensor.

## Usage

This is designed for use with Home Assistant GTFS Realtime Custom Component.

### Feed Subjects and Station Stops

All updates go through the Feed Subject which is setup to call updates from one or more feed URLS.

Create a feed subject like so, then pass it in the constructor for a Station Stop

```
from gtfs_station_stop.feed_subject import FeedSubject
from gtfs_station_stop.station_stop import StationStop

# Obtain the API keep from your GTFS provider if needed, otherwise leave blank.
api_key = "YOUR_API_KEY_HERE"
urls = ["https://gtfs.example.com/feed1", "https://gtfs.example.com/feed2"]
feed_subject = FeedSubject(api_key, urls)

# Obtain the Stop ID from GTFS static data from your provider.
# This must match those provided by the realtime feed.
station_stop_nb = StationStop("STOP_ID_NORTHBOUND", feed_subject)
station_stop_sb = StationStop("STOP_ID_SOUTHBOUND", feed_subject)
```

Calling `feed_subject.update()` will update all registered listeners.

```
feed_subject.update()

for arrival in station_stop_nb.arrivals:
    minutes_to = (arrival.time - time.time()) / 60.0
    print(f"{arrival.route} in {minutes_to}")
```

Active service alerts are also supported for station stops and for routes.

```
route_status = RouteStatus("Line 1", feed_subject)

feed_subject.update()

for alert in route_status.alerts:
    print(f"{route_status.id} alert {alert.header_text['en']}")

for alert in station_stop_nb.alerts:
    print(f"{station_stop_nb.id} alert {alert.header_text['en']}")
```

### GTFS Static Info

Static data can be loaded into a database for convenient lookup to use alongside GTFS Realtime data.

```
from gtfs_station_stop.station_stop_info import StationStopInfoDatabase

station_stop_info_db = StationStopInfoDatabase("gtfs_static.zip")
print(f"{station_stop_info_db['STOP_ID']}")
```

## Development Setup

Install all development dependencies with:

```
$ pip install -r requirements-dev.txt
```

Run tests with:
```
$ pytest
```
