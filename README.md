# GTFS Station Stop

A project for organizing GTFS Real-Time data for use as a homeassistant sensor.

## Usage

This is designed for use with [Home Assistant GTFS Realtime Custom Component](https://github.com/bcpearce/homeassistant-gtfs-realtime).

It can also be used for general GTFS update purposes.

### Feed Subjects and Station Stops

All updates go through the Feed Subject which is setup to call updates from one or more feed URLS.

Create a feed subject like so, then pass it in the constructor for a Station Stop

```python
from gtfs_station_stop.feed_subject import FeedSubject
from gtfs_station_stop.station_stop import StationStop

# Obtain the API keep from your GTFS provider if needed, otherwise leave blank.
api_key = "YOUR_API_KEY_HERE"
urls = ["https://gtfs.example.com/feed1", "https://gtfs.example.com/feed2"]
feed_subject = FeedSubject(urls, api_key)

# Obtain the Stop ID from GTFS static data from your provider.
# This must match those provided by the realtime feed.
station_stop_nb = StationStop("STOP_ID_NORTHBOUND", feed_subject)
station_stop_sb = StationStop("STOP_ID_SOUTHBOUND", feed_subject)
```

Calling `feed_subject.update()` will update all registered listeners.

```python
feed_subject.update()

for arrival in station_stop_nb.arrivals:
    minutes_to = (arrival.time - time.time()) / 60.0
    print(f"{arrival.route} in {minutes_to}")
```

Active service alerts are also supported for station stops and for routes.

```python
route_status = RouteStatus("Line 1", feed_subject)

feed_subject.update()

for alert in route_status.alerts:
    print(f"{route_status.id} alert {alert.header_text['en']}")

for alert in station_stop_nb.alerts:
    print(f"{station_stop_nb.id} alert {alert.header_text['en']}")
```

As the update will make one or more http requests, this may improve performance or integrate better with an asynchronous project.

### GTFS Static Info

Static data can be loaded into a Dataset for convenient lookup to use alongside GTFS Realtime data. GTFS data can be read from a file or a URL from your service provider. The GTFS file must be provided as a .zip containing the requisite .txt files as defined by [GTFS Static Reference](https://developers.google.com/transit/gtfs/reference).

```python
from gtfs_station_stop.station_stop_info import StationStopInfoDataset

station_stop_infods = StationStopInfoDataset("gtfs_static.zip")
print(f"{station_stop_infods['STOP_ID']}")
```

Static info can be queried through the `station_stop_info`, `route_info`, `calendar`, and `trip_info` submodules.

GTFS providers will regularly update their static feeds. In order to account for this, the library will attempt to cache zip file downloads for static info.

### Async Updates

Asynchronous updates are also supported through the `async_update()` method.

```python
await feed_subject.async_update()
```

Static data can also be obtained similarly with `gtfs_station_stop.static_Dataset.async_factory`.

```python
station_stop_info_Dataset = await async_get_gtfs_Dataset(StationStopInfoDataset, "https://gtfsprovider.example.com/static.zip")
```

### Command Line Interface

This can be run as a Python module on the command line using

`python -m gtfs_station_stop`

Use `python -m gtfs_station_stop --help` for details.

## Development Setup

Install all development dependencies with:

```bash
$ pip install -r requirements-dev.txt
```

Run tests with:

```bash
$ pytest
```
