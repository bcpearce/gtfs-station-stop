"""GTFS Static Dataset Base Class."""

import inspect
import os
from io import BytesIO

import aiofiles
import asyncio_atexit
from aiohttp_client_cache import CachedSession, SQLiteBackend

from gtfs_station_stop.const import GTFS_STATIC_CACHE, GTFS_STATIC_CACHE_EXPIRY
from gtfs_station_stop.helpers import gtfs_record_iter, is_url

_SESSION = None


async def _close_session() -> None:
    if not _SESSION.closed:
        await _SESSION.close()


def _get_session() -> CachedSession:
    global _SESSION
    if _SESSION is None:
        _SESSION = CachedSession(
            cache=SQLiteBackend(GTFS_STATIC_CACHE, GTFS_STATIC_CACHE_EXPIRY)
        )
        asyncio_atexit.register(_close_session)
    return _SESSION


class GtfsStaticDataset:
    """
    Base class for GTFS Datasets.
    https://gtfs.org/documentation/schedule/reference/#dataset-files
    """

    def __init__(self, *gtfs_files: os.PathLike, **kwargs) -> None:
        self.kwargs = kwargs
        for file in gtfs_files:
            self.add_gtfs_data(file)

    def _get_gtfs_record_iter(self, zip_filelike, target_txt: os.PathLike):
        return gtfs_record_iter(zip_filelike, target_txt, **self.kwargs)

    def add_gtfs_data(self, zip_filelike: os.PathLike) -> None:
        """Add GTFS Data."""
        raise NotImplementedError


async def async_factory(
    gtfs_ds_or_class: type[GtfsStaticDataset] | GtfsStaticDataset,
    *gtfs_resource: os.PathLike | BytesIO,
    **kwargs,
) -> GtfsStaticDataset:
    """Create an empty dataset if a type is given"""
    gtfsds = (
        gtfs_ds_or_class()
        if inspect.isclass(gtfs_ds_or_class)
        and issubclass(gtfs_ds_or_class, GtfsStaticDataset)
        else gtfs_ds_or_class
    )

    _session = _get_session()
    _session.cache.name = kwargs.get("gtfs_static_cache", GTFS_STATIC_CACHE)
    _session.cache.expire_after = kwargs.get("expire_after", GTFS_STATIC_CACHE_EXPIRY)

    for resource in gtfs_resource:
        zip_data = None
        if is_url(resource) and isinstance(_session, CachedSession):
            async with _session.get(
                resource, headers=kwargs.get("headers")
            ) as response:
                if 200 <= response.status < 400:
                    zip_data = BytesIO(await response.read())
                else:
                    raise RuntimeError(
                        f"HTTP error {response.status}, {await response.text()}"
                    )
        elif isinstance(resource, os.PathLike):  # assume file
            async with aiofiles.open(resource, "rb") as f:
                zip_data = BytesIO(await f.read())
        else:
            zip_data = resource

        gtfsds.add_gtfs_data(zip_data)
    return gtfsds
