import asyncio
import concurrent.futures
import time
from collections import defaultdict
from collections.abc import Sequence
from typing import Any
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
    """
    Subject in the observer pattern. Manages the polling of registered endpoints and
    updates subscribed entities.
    """

    def __init__(
        self,
        realtime_feed_uris: Sequence[str],
        *,
        headers: dict[str, Any] | None = None,
        max_api_calls_per_second: float | None = None,
        http_timeout: float = 30,
    ):
        self.realtime_feed_uris = set(realtime_feed_uris)
        self._headers: dict[str, Any] | None = headers
        self._max_api_calls_per_second: float | None = max_api_calls_per_second
        self._http_timeout: float | None = http_timeout
        self.subscribers = defaultdict(WeakSet)

    @property
    def headers(self) -> dict[str, Any] | None:
        """Headers to be passed to Realtime Feed URLS."""
        return self._headers

    @headers.setter
    def headers(self, new_headers: dict[str, Any] | None) -> None:
        self._headers = new_headers

    @property
    def max_api_calls_per_second(self) -> float:
        """Maximum API calls allowed per second, useful for rate-limited APIs."""
        return self._max_api_calls_per_second

    @max_api_calls_per_second.setter
    def max_api_calls_per_second(
        self, new_max_api_calls_per_second: float | None
    ) -> None:
        """Set maximum API calls per second."""
        if new_max_api_calls_per_second is None:
            self._max_api_calls_per_second = None
        else:
            if new_max_api_calls_per_second < 0:
                raise ValueError("max_api_calls_per_second cannot be negative")
            self._max_api_calls_per_second = new_max_api_calls_per_second

    @property
    def delay_between_api_calls(self) -> float | None:
        """Delay between API calls in seconds."""
        if self._max_api_calls_per_second is None:
            return None
        return 1.0 / self._max_api_calls_per_second

    @delay_between_api_calls.setter
    def delay_between_api_calls(self, new_max_delay_between_api_calls) -> float | None:
        """
        Set delay between API calls in seconds, inverse of maximum calls per second.
        """
        if new_max_delay_between_api_calls is None:
            self._max_api_calls_per_second = None
        else:
            if new_max_delay_between_api_calls < 0:
                raise ValueError("max_delay_between_api_calls cannot be negative")
            self._max_api_calls_per_second = 1.0 / new_max_delay_between_api_calls

    @property
    def http_timeout(self) -> float | None:
        """Timeout for a given HTTP request."""
        return self._http_timeout

    @http_timeout.setter
    def http_timeout(self, new_timeout: float | None) -> float:
        """Timeout for a given HTTP request"""
        self._http_timeout = new_timeout

    def _request_gtfs_feed(self, uri: str) -> bytes:
        req: requests.Response = requests.get(
            url=uri, headers=self.headers, timeout=self.http_timeout
        )
        if req.status_code <= 200 and req.status_code < 300:
            return req.content
        req.raise_for_status()

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
        async with (
            aiohttp.ClientSession(
                headers=self.headers, timeout=aiohttp.ClientTimeout(self.http_timeout)
            ) as session,
            session.get(uri) as req,
        ):
            if req.status <= 200 and req.status < 300:
                return await req.read()
            else:
                req.raise_for_status()

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
                if self.delay_between_api_calls:
                    await asyncio.sleep(self.delay_between_api_calls)
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

    def _notify_alerts(self, feed) -> None:
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
                            # validate that one of the active periods is current,
                            # then add it
                            sub.alerts.append(
                                Alert(
                                    ends_at=ends_at,
                                    header_text={h.language: h.text for h in hdr},
                                    description_text={d.language: d.text for d in dsc},
                                )
                            )

    def _reset_subscribers(self) -> None:
        timestamp = time.time()
        for subs in self.subscribers.values():
            for sub in subs:
                sub.begin_update(timestamp)

    def _reset_and_notify(self, feed: gtfs_realtime_pb2.FeedMessage) -> None:
        self._reset_subscribers()
        self._notify_stop_updates(feed)
        self._notify_alerts(feed)

    def update(self) -> None:
        """Synchronous update of all feeds and subscribers."""
        self._reset_and_notify(self._get_gtfs_feed())

    async def async_update(self) -> None:
        """Asyncrhonous update of all feeds and subscribers."""
        self._reset_and_notify(await self._async_get_gtfs_feed())

    def subscribe(self, updatable: StationStop | RouteStatus) -> None:
        """Add an informed entity as a subscriber."""
        self.subscribers[updatable.id].add(updatable)

    def unsubscribe(self, updatable: StationStop | RouteStatus) -> None:
        """Remove an informed entity as a subscriber."""
        self.subscribers[updatable.id].remove(updatable)
