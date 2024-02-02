import concurrent.futures
import time
from collections import defaultdict
from collections.abc import Sequence
from weakref import WeakSet

import requests
from google.transit import gtfs_realtime_pb2


class StationStop:
    # implemented in station_stop.py
    pass


class FeedSubject:
    def __init__(self, api_key: str, realtime_feed_uris: Sequence[str]):
        self.api_key = api_key
        self.realtime_feed_uris = set(realtime_feed_uris)
        self.subscribers = defaultdict(WeakSet)

    def _request_gtfs_feed(self, uri: str) -> bytes:
        req: requests.Response = requests.get(
            url=uri, headers={"x-api-key": self.api_key}
        )
        if req.status_code <= 200 and req.status_code < 300:
            return req.content
        raise RuntimeError(f"HTTP error code {req.status_code}")

    def _get_gtfs_feed(self) -> gtfs_realtime_pb2.FeedMessage:
        def load_feed_data(_subject, _uri):
            uri_feed = gtfs_realtime_pb2.FeedMessage()
            uri_feed.ParseFromString(_subject._request_gtfs_feed(_uri))
            return uri_feed

        # This is horrifically slow sequentially
        feed = gtfs_realtime_pb2.FeedMessage()
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=len(self.realtime_feed_uris)
        ) as executor:
            futs = [
                executor.submit(load_feed_data, self, uri)
                for uri in self.realtime_feed_uris
            ]
            for fut in concurrent.futures.as_completed(futs):
                feed.MergeFrom(fut.result())

        return feed

    def _notify_stop_updates(self, feed):
        for e in feed.entity:
            if e.HasField("trip_update"):
                tu = e.trip_update
                for stu in (
                    stu
                    for stu in tu.stop_time_update
                    if stu.stop_id in self.subscribers
                ):
                    for sub in self.subscribers[stu.stop_id]:
                        sub.arrivals.append((tu.trip.route_id, stu.arrival.time))

    def _notify_alerts(self, feed):
        for e in feed.entity:
            if e.HasField("alert"):
                al = e.alert
                for ie in (
                    ie for ie in al.informed_entity if ie.stop_id in self.subscribers
                ):
                    for sub in self.subscribers[ie.stop_id]:
                        hdr = al.header_text.translation
                        dsc = al.description_text.translation
                        sub.alerts.append(
                            (
                                hdr[0].text if len(hdr) > 0 else "",
                                dsc[0].text if len(dsc) > 0 else "",
                            )
                        )

    def _reset_subscribers(self):
        timestamp = time.time()
        for subs in self.subscribers.values():
            for sub in subs:
                sub.alerts.clear()
                sub.arrivals.clear()
                sub.last_updated = timestamp

    def update(self):
        start = time.time()
        feed = self._get_gtfs_feed()
        print(f"took {time.time() - start} seconds for getting feeds")
        self._reset_subscribers()
        self._notify_stop_updates(feed)
        self._notify_alerts(feed)

    def subscribe(self, station_stop: StationStop):
        self.subscribers[station_stop.stop_id].add(station_stop)

    def unsubscribe(self, station_stop: StationStop):
        self.subscribers[station_stop.stop_id].remove(station_stop)
