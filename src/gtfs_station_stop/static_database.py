import os
from io import BytesIO

from aiohttp_client_cache import CachedSession, SQLiteBackend

from gtfs_station_stop.const import GTFS_STATIC_CACHE, GTFS_STATIC_CACHE_EXPIRY


class GtfsStaticDatabase:
    def __init__(self, *gtfs_files: os.PathLike):
        for file in gtfs_files:
            self.add_gtfs_data(file)

    def add_gtfs_data(self, gtfs_pathlike: os.PathLike):
        raise NotImplementedError


async def async_factory(
    gtfs_class: GtfsStaticDatabase,
    *gtfs_urls: os.PathLike,
    **kwargs,
):
    gtfs_db = gtfs_class()
    for url in gtfs_urls:
        async with CachedSession(
            cache=SQLiteBackend(
                kwargs.get("gtfs_static_cache", GTFS_STATIC_CACHE),
                expire_after=kwargs.get("expire_after", GTFS_STATIC_CACHE_EXPIRY),
            )
        ) as session:
            async with session.get(url) as response:
                zip_data = BytesIO(await response.read())
                gtfs_db.add_gtfs_data(zip_data)
    return gtfs_db
