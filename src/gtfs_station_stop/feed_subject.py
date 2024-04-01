import asyncio
import concurrent.futures
import time
from collections import defaultdict
from collections.abc import Sequence
from weakref import WeakSet

import aiohttp
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
    def __init__(self, realtime_feed_uris: Sequence[str], **kwargs):
        self.realtime_feed_uris = set(realtime_feed_uris)
        self.kwargs = kwargs
        self.subscribers = defaultdict(WeakSet)

    def _request_gtfs_feed(self, uri: str) -> bytes:
        req: requests.Response = requests.get(
            url=uri, headers=self.kwargs.get("headers")
        )
        if req.status_code <= 200 and req.status_code < 300:
            return req.content
        raise RuntimeError(f"HTTP error code {req.status_code}, {req.text}")

    def _get_gtfs_feed(self) -> gtfs_realtime_pb2.FeedMessage:
        def load_feed_data(_subject, _uri):
            uri_feed = gtfs_realtime_pb2.FeedMessage()
            uri_feed.ParseFromString(_subject._request_gtfs_feed(_uri))
            return uri_feed

        # This is horrifically slow sequentially
        feed = gtfs_realtime_pb2.FeedMessage()
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=len(self.realtime_feed_uris) | 1
        ) as executor:
            futs = [
                executor.submit(load_feed_data, self, uri)
                for uri in self.realtime_feed_uris
            ]
            for fut in concurrent.futures.as_completed(futs):
                feed.MergeFrom(fut.result())

        return feed

    async def _async_request_gtfs_feed(self, uri: str) -> bytes:
        async with aiohttp.ClientSession(headers=self.kwargs.get("headers")) as session:
            async with session.get(uri) as req:
                if req.status <= 200 and req.status < 300:
                    return await req.read()
                else:
                    raise RuntimeError(
                        f"HTTP error code {req.status}, {await req.text()}"
                    )

    async def _async_get_gtfs_feed(self) -> gtfs_realtime_pb2.FeedMessage:
        async def async_merge_feed(
            merge_into_feed: gtfs_realtime_pb2.FeedMessage,
            merge_from_feed: gtfs_realtime_pb2.FeedMessage,
        ):
            merge_into_feed.MergeFrom(merge_from_feed)

        async def async_load_feed_data(
            _subject,
            _uri,
            main_feed: gtfs_realtime_pb2.FeedMessage,
            task_group: asyncio.TaskGroup,
        ):
            uri_feed = gtfs_realtime_pb2.FeedMessage()
            uri_feed.ParseFromString(await _subject._async_request_gtfs_feed(_uri))
            task_group.create_task(async_merge_feed(main_feed, uri_feed))

        feed = gtfs_realtime_pb2.FeedMessage()
        async with asyncio.TaskGroup() as tg:
            for uri in self.realtime_feed_uris:
                tg.create_task(async_load_feed_data(self, uri, feed, tg))
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

    def _reset_and_notify(self, feed: gtfs_realtime_pb2.FeedMessage):
        self._reset_subscribers()
        self._notify_stop_updates(feed)
        self._notify_alerts(feed)

    def update(self):
        self._reset_and_notify(self._get_gtfs_feed())

    async def async_update(self):
        self._reset_and_notify(await self._async_get_gtfs_feed())

    def subscribe(self, updatable: StationStop | RouteStatus):
        self.subscribers[updatable.id].add(updatable)

    def unsubscribe(self, updatable: StationStop | RouteStatus):
        self.subscribers[updatable.id].remove(updatable)
