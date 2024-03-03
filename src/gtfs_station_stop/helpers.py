import csv
import os
import time
from datetime import datetime as dt
from io import StringIO
from zipfile import ZipFile

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


def gtfs_record_iter(zip_filepath: os.PathLike, target_txt: os.PathLike):
    """Generates a line from a given GTFS table."""
    with ZipFile(zip_filepath) as zip:
        # Find the stops.txt file
        first_or_none: str = next(
            (name for name in zip.namelist() if name == target_txt), None
        )
        if first_or_none is None:
            raise RuntimeError(f"Did not find required {target_txt} file")
        # Create the dictionary of IDs, parents should preceed the children
        with StringIO(str(zip.read(first_or_none), encoding="ASCII")) as stops_dot_txt:
            reader = csv.DictReader(
                stops_dot_txt,
                delimiter=",",
            )
            for line in reader:
                yield line
