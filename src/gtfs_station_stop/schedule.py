"""Schedule"""

import os
import shutil
import tempfile
from asyncio import TaskGroup
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from io import BytesIO
from os import PathLike
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import aiofiles
from aiohttp import ClientSession
from yarl import URL

from gtfs_station_stop.arrival import Arrival
from gtfs_station_stop.calendar import Calendar
from gtfs_station_stop.route_info import RouteInfo, RouteInfoDataset
from gtfs_station_stop.static_dataset import (
    GtfsStaticDataset,
    async_factory,
)
from gtfs_station_stop.station_stop_info import StationStopInfo, StationStopInfoDataset
from gtfs_station_stop.stop_times import StopTimesDataset
from gtfs_station_stop.trip_info import TripInfo, TripInfoDataset

DEFAULT_CHUNK_SIZE = 65536


async def _get_nested_zip(
    target: Path, dest: PathLike, *, chunk_size: int = DEFAULT_CHUNK_SIZE
) -> list[Path]:
    dest = Path(dest)
    if not dest.is_dir():
        raise ValueError("Must pass a directory as the `dest` parameter")

    res = []
    with ZipFile(target, "r") as z:
        for file in [
            file
            for file in z.filelist
            if not file.is_dir() and file.filename.endswith(".zip")
        ]:
            dest_fullpath = dest / file.filename
            os.makedirs(dest_fullpath.parent, exist_ok=True)
            with z.open(file, "r") as z_nested:
                async with (
                    aiofiles.open(dest_fullpath, "wb") as f,
                ):
                    buf = bytearray(chunk_size)
                    while (n_bytes := z_nested.readinto(buf)) > 0:
                        await f.write(buf[:n_bytes])
            res.append(dest_fullpath)
    return res


@dataclass(kw_only=True)
class GtfsSchedule:
    """GTFS Schedule."""

    calendar: Calendar = field(default_factory=Calendar)
    station_stop_info_ds: StationStopInfoDataset = field(
        default_factory=StationStopInfoDataset
    )
    trip_info_ds: TripInfoDataset = field(default_factory=TripInfoDataset)
    route_info_ds: RouteInfoDataset = field(default_factory=RouteInfoDataset)
    stop_times_ds: StopTimesDataset = field(default_factory=StopTimesDataset)
    tmp_dir: TemporaryDirectory | None = None
    tmp_dir_path: Path | None = None
    resources: set[Path] = field(default_factory=set)

    async def async_build_schedule(
        self,
        *gtfs_urls: URL,
        session: ClientSession | None = None,
        **kwargs,
    ) -> None:
        """Update the schedule given a set of URLs"""
        close_session = False
        if session is None:
            session = ClientSession()
            close_session = True

        try:
            if self.tmp_dir is None:
                gtfs_tmp_dir = f"{tempfile.gettempdir()}/gtfs_station_stop"
                os.makedirs(gtfs_tmp_dir, exist_ok=True)
                self.tmp_dir = TemporaryDirectory(dir=gtfs_tmp_dir)
                self.tmp_dir_path = Path(self.tmp_dir.name)
            async with TaskGroup() as tg:
                for url in gtfs_urls:
                    hash_str = hex(hash(str(url)) & 0xFFFFFFFF)[2:]
                    path = self.tmp_dir_path / f"{hash_str}.zip"
                    tg.create_task(
                        self._async_download_to_file_and_add_data(
                            tg,
                            url,
                            path,
                            session=session,
                            **kwargs,
                        )
                    )
        finally:
            if close_session:
                await session.close()

    async def async_load_stop_times(self, stops_filter: set[str] | None = None) -> None:
        """
        Async load stop times in stop_times.txt
        This operation should be delayed from schedule building as it can
        be time consuming and is not needed for many datasets.
        """
        self.stop_times_ds.stops_filter = stops_filter or set()
        for resource in self.resources:
            in_mem: BytesIO | None = None
            async with aiofiles.open(resource, "rb") as f:
                in_mem = BytesIO(await f.read())
                self.stop_times_ds.add_gtfs_data(in_mem)

    def get_stop_info(self, stop_id: str) -> StationStopInfo | None:
        """Get stop info by ID."""
        return self.station_stop_info_ds.station_stop_infos.get(stop_id)

    def get_trip_headsign(self, trip_id: str) -> str:
        """Get Trip's Headsign."""
        trip_info: TripInfo = self.trip_info_ds.get_close_match(trip_id)
        if trip_info is not None:
            return trip_info.trip_headsign
        return ""

    def get_route_color(self, route_id: str) -> str:
        """Get Trip's Route Color."""
        route_info: RouteInfo = self.route_info_ds.get(route_id)
        if route_info is not None:
            return route_info.color
        return ""

    def get_route_text_color(self, route_id: str) -> str:
        """Get Trip's Route Text Color."""
        route_info: RouteInfo = self.route_info_ds.get(route_id)
        if route_info is not None:
            return route_info.text_color
        return ""

    def get_route_type(self, route_id: str) -> str:
        """Get Trip's Route Type."""
        route_info: RouteInfo = self.route_info_ds.get(route_id)
        if route_info is not None:
            return route_info.type.pretty_name()
        return ""

    def get_upcoming_arrivals(self, stop_id: str, delta: timedelta) -> list[Arrival]:
        """Get a list of scheduled arrivals from now until a time in the future."""
        return self.get_arrivals_between_times(
            stop_id, datetime.now(), datetime.now() + delta
        )

    def get_arrivals_between_times(
        self, stop_id: str, start: datetime, end: datetime
    ) -> list[Arrival]:
        """Get a list of scheduled arrivals."""
        arrivals: list[Arrival] = []
        active_services = set(
            self.calendar.get_active_services(start.date())
            + self.calendar.get_active_services(end.date())
        )
        for trip_id, stop_seq in self.stop_times_ds.stop_times.items():
            for stop_time in stop_seq.values():
                if (
                    stop_time.stop_id == stop_id
                    and (trip_info := self.trip_info_ds.get(trip_id)) is not None
                    and trip_info.service_id in [s.service_id for s in active_services]
                ):
                    at = datetime(
                        year=start.year,
                        month=start.month,
                        day=start.day,
                        hour=stop_time.arrival_time.hour,
                        minute=stop_time.arrival_time.minute,
                        second=stop_time.arrival_time.second,
                    )
                    if start <= at <= end:
                        arrivals.append(
                            Arrival(
                                route=trip_info.route_id,
                                trip=trip_id,
                                time=at,
                            )
                        )
        return arrivals

    def __del__(self) -> None:
        if self.tmp_dir_path is not None and self.tmp_dir_path.is_dir():
            shutil.rmtree(self.tmp_dir_path, ignore_errors=True)

    def _get_required_datasets(self) -> list[GtfsStaticDataset]:
        return [
            self.calendar,
            self.station_stop_info_ds,
            self.trip_info_ds,
            self.route_info_ds,
        ]

    async def _async_download_to_file_and_add_data(
        self,
        task_group: TaskGroup,
        url: URL,
        target: Path,
        *,
        session: ClientSession | None = None,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        **kwargs,
    ) -> None:
        async with (
            session.get(url, **kwargs) as resp,
            aiofiles.open(target, "wb") as tmp_f,
        ):
            async for chunk in resp.content.iter_chunked(chunk_size):
                await tmp_f.write(chunk)

        self.resources.add(target)
        nested_dest = target.parent
        os.makedirs(nested_dest, exist_ok=True)
        nested_resources = [Path(s) for s in await _get_nested_zip(target, nested_dest)]
        self.resources.update(nested_resources)
        for resource in [target] + nested_resources:
            in_mem: BytesIO | None = None
            async with aiofiles.open(resource, "rb") as f:
                in_mem = BytesIO(await f.read())
            for ds in self._get_required_datasets():
                task_group.create_task(async_factory(ds, in_mem))


async def async_build_schedule(
    *gtfs_urls: os.PathLike,
    session: ClientSession | None = None,
    **kwargs,
) -> GtfsSchedule:
    """Build a schedule dataclass."""

    close_session: bool = False
    if session is None:
        session = ClientSession()
        close_session = True

    try:
        schedule = GtfsSchedule()
        await schedule.async_build_schedule(*gtfs_urls, session=session, **kwargs)
    finally:
        if close_session:
            await session.close()
    return schedule
