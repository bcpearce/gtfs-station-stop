from dataclasses import dataclass
from datetime import datetime


@dataclass(order=True)
class Arrival:
    """Class for keeping arrival data."""

    time: datetime
    route: str
    trip: str
