"""GTFS Static Dataset Base Class."""

import inspect
import os
from io import BytesIO

import aiofiles
from aiohttp import ClientSession
from aiohttp_client_cache import CachedSession, FileBackend

from gtfs_station_stop.const import GTFS_STATIC_CACHE, GTFS_STATIC_CACHE_EXPIRY
from gtfs_station_stop.helpers import gtfs_record_iter, is_url


def create_cached_session(
    gtfs_static_cache=GTFS_STATIC_CACHE, cache_expiry=GTFS_STATIC_CACHE_EXPIRY
) -> CachedSession:
    """
    Create a cached session to use with this resource.
    This handle must be closed by the caller.
    """
    return CachedSession(
        cache=FileBackend(gtfs_static_cache, expire_after=cache_expiry)
    )


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
    session: ClientSession | None = None,
    **kwargs,
) -> GtfsStaticDataset:
    """Create an empty dataset if a type is given"""
    gtfsds = (
        gtfs_ds_or_class()
        if inspect.isclass(gtfs_ds_or_class)
        and issubclass(gtfs_ds_or_class, GtfsStaticDataset)
        else gtfs_ds_or_class
    )

    for resource in gtfs_resource:
        zip_data = None
        if is_url(resource):
            close_session: bool = False
            try:
                if session is None:
                    # automatically create a session to use for this call, then close it
                    # this is less efficient than dependency injection
                    session = create_cached_session(
                        kwargs.get("gtfs_static_cache", GTFS_STATIC_CACHE),
                        kwargs.get("cache_expiry", GTFS_STATIC_CACHE_EXPIRY),
                    )
                    close_session = True
                async with session.get(
                    resource, headers=kwargs.get("headers")
                ) as response:
                    if 200 <= response.status < 400:
                        zip_data = BytesIO(await response.read())
                    else:
                        raise RuntimeError(
                            f"HTTP error {response.status}, {await response.text()}"
                        )
            finally:
                if close_session:
                    await session.close()
        elif isinstance(resource, os.PathLike):  # assume file
            async with aiofiles.open(resource, "rb") as f:
                zip_data = BytesIO(await f.read())
        else:
            zip_data = resource

        gtfsds.add_gtfs_data(zip_data)
    return gtfsds
