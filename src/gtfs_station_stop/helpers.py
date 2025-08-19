"""Helpers"""

import csv
import io
import os
import time
from collections.abc import Generator
from datetime import datetime as dt
from io import BytesIO
from numbers import Number
from typing import Any
from urllib.parse import urlparse
from zipfile import ZipFile

import requests
from google.transit import gtfs_realtime_pb2


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


def get_as_number(
    d: dict[Any, Any], key: Any, to_type: Number, default: Number = 0
) -> Number:
    """Get a key from a dictionary, or return a Number type default."""
    try:
        tmp = d.get(key)
        if not bool(tmp):
            tmp = default
        return to_type(tmp)
    except ValueError:
        return default


def is_url(url: str):
    """Check if a str is a URL."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except (ValueError, AttributeError):
        return False


def gtfs_record_iter(
    zip_filelike, target_txt: os.PathLike, **kwargs
) -> Generator[dict[Any, Any] | None]:
    """Generates a line from a given GTFS table. Can handle local files or URLs."""

    zip_data = zip_filelike
    # If the data is a url, make the request for the file resource.
    if is_url(zip_filelike):
        # Make the request, check for good return code, and convert to IO object.
        # As GTFS Static Data updates rarely, (most providers recommend pulling this
        # once per day), we will use a cache to minimize unnecessary checks.
        res = requests.get(zip_filelike, headers=kwargs.get("headers"))
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
        with (
            z.open(first_or_none, "r") as f,
            io.TextIOWrapper(f, encoding="utf-8-sig") as buf,
        ):
            reader = csv.DictReader(buf, delimiter=",", dialect=GtfsDialect)
            yield from reader
