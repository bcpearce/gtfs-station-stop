import concurrent.futures
import time
from collections import defaultdict
from collections.abc import Sequence
from weakref import WeakSet

import requests
from google.transit import gtfs_realtime_pb2

from gtfs_station_stop import helpers
from gtfs_station_stop.alert import Alert
from gtfs_station_stop.arrival import Arrival


class StationStop:
    # implemented in station_stop.py
    pass


class RouteStatus:
    # implemented in route_status.py
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
                        sub.arrivals.append(
                            Arrival(stu.arrival.time, tu.trip.route_id, tu.trip.trip_id)
                        )

    def _notify_alerts(self, feed):
        for e in feed.entity:
            if e.HasField("alert"):
                al = e.alert
                ends_at = helpers.is_none_or_ends_at(al)
                if ends_at is not None:
                    for ie in (ie for ie in al.informed_entity):
                        for sub in (
                            self.subscribers[ie.stop_id] | self.subscribers[ie.route_id]
                        ):
                            hdr = al.header_text.translation
                            dsc = al.description_text.translation
                            # validate that one of the active periods is current, then add it
                            sub.alerts.append(
                                Alert(
                                    ends_at=ends_at,
                                    header_text={h.language: h.text for h in hdr},
                                    description_text={d.language: d.text for d in dsc},
                                )
                            )

    def _reset_subscribers(self):
        timestamp = time.time()
        for subs in self.subscribers.values():
            for sub in subs:
                sub.begin_update(timestamp)

    def update(self):
        feed = self._get_gtfs_feed()
        self._reset_subscribers()
        self._notify_stop_updates(feed)
        self._notify_alerts(feed)

    def subscribe(self, updatable: StationStop | RouteStatus):
        self.subscribers[updatable.id].add(updatable)

    def unsubscribe(self, updatable: StationStop | RouteStatus):
        self.subscribers[updatable.id].remove(updatable)
