import csv
import os
import time
from datetime import datetime as dt
from io import BytesIO, StringIO
from urllib.parse import urlparse
from zipfile import ZipFile

import requests
from google.transit import gtfs_realtime_pb2


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


def gtfs_record_iter(zip_filelike, target_txt: os.PathLike):
    """Generates a line from a given GTFS table. Can handle local files or URLs"""

    zip_data = zip_filelike
    # If the data is a url, make the request for the file resource.
    if is_url(zip_filelike):
        # Make the request, check for good return code, and convert to IO object.
        res = requests.get(zip_filelike)
        if 200 <= res.status_code < 400:
            zip_data = BytesIO(res.content)

    with ZipFile(zip_data, "r") as zip:
        # Find the stops.txt file
        first_or_none: str = next(
            (name for name in zip.namelist() if name == target_txt), None
        )
        if first_or_none is None:
            raise RuntimeError(f"Did not find required {target_txt} file")
        # Create the dictionary of IDs, parents should precede the children
        with StringIO(str(zip.read(first_or_none), encoding="ASCII")) as stops_dot_txt:
            reader = csv.DictReader(
                stops_dot_txt,
                delimiter=",",
            )
            for line in reader:
                yield line
