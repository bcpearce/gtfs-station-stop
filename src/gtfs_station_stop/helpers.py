import csv
import os
import time
from datetime import datetime as dt
from io import BytesIO, StringIO
from pathlib import Path
from urllib.parse import urlparse
from zipfile import ZipFile

import aiofiles
from aiohttp_client_cache import CachedSession as AsyncCachedSession
from aiohttp_client_cache import SQLiteBackend
from google.transit import gtfs_realtime_pb2
from requests_cache import CachedSession

from gtfs_station_stop.const import GTFS_STATIC_CACHE, GTFS_STATIC_CACHE_EXPIRY


class GtfsDialect(csv.excel):
    """Dialect for GTFS files."""

    skipinitialspace = True


def is_none_or_ends_at(
    alert: gtfs_realtime_pb2.FeedEntity, at_time: float | dt | None = None
):
    """Returns the 'ends at' time, else returns None if not active."""
    if at_time is None:
        at_time = time.time()
        # fallthrough
    if isinstance(at_time, float):
        at_time = dt.fromtimestamp(at_time)

    for time_range in alert.active_period:
        start: dt = (
            dt.fromtimestamp(time_range.start)
            if time_range.HasField("start")
            else dt.min
        )
        end: dt = (
            dt.fromtimestamp(time_range.end) if time_range.HasField("end") else dt.max
        )
        if start <= at_time <= end:
            return end

    return None


def is_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except (ValueError, AttributeError):
        return False


def gtfs_record_iter(zip_filelike, target_txt: os.PathLike, **kwargs):
    """Generates a line from a given GTFS table. Can handle local files or URLs."""

    zip_data = zip_filelike
    # If the data is a url, make the request for the file resource.
    if is_url(zip_filelike):
        # Make the request, check for good return code, and convert to IO object.
        # As GTFS Static Data updates rarely, (most providers recommend pulling this
        # once per day), we will use a cache to minimize unnecessary checks.
        session = CachedSession(
            GTFS_STATIC_CACHE,
            expire_after=GTFS_STATIC_CACHE_EXPIRY,
        )
        res = session.get(zip_filelike, headers=kwargs.get("headers"))
        if 200 <= res.status_code < 400:
            zip_data = BytesIO(res.content)
        else:
            raise ConnectionRefusedError

    with ZipFile(zip_data, "r") as z:
        # Find the *.txt file
        first_or_none: str = next(
            (name for name in z.namelist() if name == target_txt), None
        )
        if first_or_none is None:
            return
        # Create the dictionary of IDs, parents should precede the children
        with StringIO(
            str(z.read(first_or_none), encoding="utf-8-sig")
        ) as dataset_dot_txt:
            reader = csv.DictReader(dataset_dot_txt, delimiter=",", dialect=GtfsDialect)
            yield from reader


async def unpack_nested_zips(
    *gtfs_resources: os.PathLike | BytesIO, **kwargs
) -> list[BytesIO]:
    """Dives into a zip file looking for nested .zip."""
    res = []
    async with AsyncCachedSession(
        cache=SQLiteBackend(
            kwargs.get("gtfs_static_cache", GTFS_STATIC_CACHE),
            expire_after=kwargs.get("expire_after", GTFS_STATIC_CACHE_EXPIRY),
        ),
        headers=kwargs.get("headers"),
    ) as session:
        for resource in gtfs_resources:
            zip_data = resource
            if is_url(resource):
                async with session.get(resource) as response:
                    if 200 <= response.status < 400:
                        zip_data = BytesIO(await response.read())
                    else:
                        raise RuntimeError(
                            f"HTTP error code {response.status}, {await response.text()}"  # noqa E501
                        )
            elif isinstance(resource, os.PathLike):  # assume file
                async with aiofiles.open(resource, mode="rb") as f:
                    zip_data = BytesIO(await f.read())

            with ZipFile(zip_data, "r") as z:
                nested_zips = [
                    BytesIO(z.read(x))
                    for x in z.namelist()
                    if Path(x).suffix.lower() == ".zip"
                ]
                res += nested_zips
                res += await unpack_nested_zips(*nested_zips)

    return res
