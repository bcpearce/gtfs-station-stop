import os
from io import BytesIO

from aiohttp_client_cache import CachedSession, SQLiteBackend

from gtfs_station_stop.const import GTFS_STATIC_CACHE, GTFS_STATIC_CACHE_EXPIRY
from gtfs_station_stop.helpers import gtfs_record_iter


class GtfsStaticDatabase:
    def __init__(self, *gtfs_files: os.PathLike, **kwargs):
        self.kwargs = kwargs
        for file in gtfs_files:
            self.add_gtfs_data(file)

    def _get_gtfs_record_iter(self, zip_filelike, target_txt: os.PathLike):
        return gtfs_record_iter(zip_filelike, target_txt, **self.kwargs)

    def add_gtfs_data(self, gtfs_pathlike: os.PathLike):
        raise NotImplementedError


async def async_factory(
    gtfs_class: GtfsStaticDatabase,
    *gtfs_urls: os.PathLike,
    **kwargs,
):
    gtfs_db = gtfs_class()
    async with CachedSession(
        cache=SQLiteBackend(
            kwargs.get("gtfs_static_cache", GTFS_STATIC_CACHE),
            expire_after=kwargs.get("expire_after", GTFS_STATIC_CACHE_EXPIRY),
        ),
        headers=kwargs.get("headers"),
    ) as session:
        for url in gtfs_urls:
            async with session.get(url) as response:
                if 200 <= response.status < 400:
                    zip_data = BytesIO(await response.read())
                    gtfs_db.add_gtfs_data(zip_data)
                else:
                    raise RuntimeError(
                        f"HTTP error code {response.status}, {await response.text()}"
                    )
    return gtfs_db
