import time
from datetime import datetime as dt

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
