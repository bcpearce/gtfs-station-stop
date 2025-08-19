"""GTFS Static Dataset Base Class."""

import asyncio
import inspect
import os
from io import BytesIO

import aiofiles
from aiohttp import ClientSession

from gtfs_station_stop.helpers import gtfs_record_iter, is_url


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
                    session = ClientSession()
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

        def add_gtfs_data(zip_data=zip_data) -> None:
            gtfsds.add_gtfs_data(zip_data)

        await asyncio.to_thread(add_gtfs_data)
    return gtfsds
