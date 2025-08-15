"""Schedule"""

import asyncio
import os
import shutil
import tempfile
from asyncio import TaskGroup
from dataclasses import dataclass, field
from io import BytesIO
from os import PathLike
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import aiofiles
from aiohttp import ClientSession
from yarl import URL

from gtfs_station_stop.calendar import Calendar
from gtfs_station_stop.const import GTFS_STATIC_CACHE, GTFS_STATIC_CACHE_EXPIRY
from gtfs_station_stop.helpers import unpack_nested_zips
from gtfs_station_stop.route_info import RouteInfo, RouteInfoDataset
from gtfs_station_stop.static_dataset import (
    GtfsStaticDataset,
    async_factory,
    create_cached_session,
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
                    aiofiles.open(dest / file.filename, "wb") as f,
                ):
                    buf = bytearray(chunk_size)
                    while (n_bytes := z_nested.readinto(buf)) > 0:
                        await f.write(buf[:n_bytes])
            res.append(z.extract(file, dest))
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

    def _get_datasets(self) -> list[GtfsStaticDataset]:
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
        stops_filter: set[str],
        *,
        session: ClientSession | None = None,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
    ) -> None:
        async with (
            session.get(url) as resp,
            aiofiles.open(target, "wb") as tmp_f,
        ):
            async for chunk in resp.content.iter_chunked(chunk_size):
                await tmp_f.write(chunk)

        self.resources.add(target)
        nested_dest = target.parent
        os.makedirs(nested_dest, exist_ok=True)
        self.resources.update(
            Path(s) for s in await _get_nested_zip(target, nested_dest)
        )
        for resource in self.resources:
            in_mem: BytesIO | None = None
            async with aiofiles.open(resource, "rb") as f:
                in_mem = BytesIO(await f.read())
            for ds in [self.calendar, self.route_info_ds, self.trip_info_ds]:
                task_group.create_task(async_factory(ds, in_mem))
            await async_factory(self.station_stop_info_ds, in_mem)
            if set(self.station_stop_info_ds.get_stop_ids()) & stops_filter:
                self.stop_times_ds.stops_filter = stops_filter
                self.stop_times_ds.add_gtfs_data(in_mem)

    async def async_build_schedule(
        self,
        *gtfs_urls: URL,
        session: ClientSession | None = None,
        stops_filter: set[str] | None = None,
    ) -> None:
        """Update the schedule given a set of URLs"""
        close_session = False
        if session is None:
            session = ClientSession()
            close_session = True

        try:
            if self.tmp_dir is None:
                self.tmp_dir = TemporaryDirectory(
                    dir=f"{tempfile.gettempdir()}/gtfs_station_stop"
                )
                self.tmp_dir_path = Path(self.tmp_dir.name)
            async with TaskGroup() as tg:
                for url in gtfs_urls:
                    hash_str = hex(hash(str(url)) & 0xFFFFFFFF)[2:]
                    path = self.tmp_dir_path / f"{hash_str}.zip"
                    tg.create_task(
                        self._async_download_to_file_and_add_data(
                            tg, url, path, stops_filter or set(), session=session
                        )
                    )
        finally:
            if close_session:
                await session.close()

    def __del__(self) -> None:
        if self.tmp_dir_path is not None and self.tmp_dir_path.is_dir():
            shutil.rmtree(self.tmp_dir_path, ignore_errors=True)

    async def async_update_schedule(
        self,
        *gtfs_resources: os.PathLike,
        session: ClientSession | None = None,
        **kwargs,
    ) -> None:
        """Build a schedule dataclass."""

        # Check for nested file resources

        close_session = False
        if session is None:
            session = create_cached_session(
                kwargs.get("gtfs_static_cache", GTFS_STATIC_CACHE),
                kwargs.get("cache_expiry", GTFS_STATIC_CACHE_EXPIRY),
            )
            close_session = True

        nested_resources = await unpack_nested_zips(*gtfs_resources)
        gtfs_resources = list(gtfs_resources) + nested_resources

        try:
            async with asyncio.TaskGroup() as tg:
                for gtfs_resource in gtfs_resources:
                    for static_dataset in [
                        self.calendar,
                        self.station_stop_info_ds,
                        self.trip_info_ds,
                        self.route_info_ds,
                        self.stop_times_ds,
                    ]:
                        tg.create_task(async_factory(static_dataset, gtfs_resource))
        finally:
            if close_session:
                await session.close()

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


async def async_build_schedule(
    *gtfs_urls: os.PathLike,
    session: ClientSession | None = None,
    stops_filter: set[str] | None = None,
    **kwargs,
) -> GtfsSchedule:
    """Build a schedule dataclass."""

    close_session: bool = False
    if session is None:
        session = create_cached_session()
        close_session = True

    try:
        async with asyncio.TaskGroup() as tg:
            cal_ds_task = tg.create_task(
                async_factory(Calendar, *gtfs_urls, session=session, **kwargs)
            )
            ssi_ds_task = tg.create_task(
                async_factory(
                    StationStopInfoDataset, *gtfs_urls, session=session, **kwargs
                )
            )
            ti_ds_task = tg.create_task(
                async_factory(TripInfoDataset, *gtfs_urls, session=session, **kwargs)
            )
            rti_ds_task = tg.create_task(
                async_factory(RouteInfoDataset, *gtfs_urls, session=session, **kwargs)
            )
            st_ds = StopTimesDataset()
            st_ds.stops_filter = stops_filter
            st_ds_task = tg.create_task(
                async_factory(st_ds, *gtfs_urls, session=session, **kwargs)
            )
    finally:
        if close_session:
            await session.close()
    return GtfsSchedule(
        calendar=cal_ds_task.result(),
        station_stop_info_ds=ssi_ds_task.result(),
        trip_info_ds=ti_ds_task.result(),
        route_info_ds=rti_ds_task.result(),
        stop_times_ds=st_ds_task.result(),
    )
