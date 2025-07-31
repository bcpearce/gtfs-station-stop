"""Dataclass for Arrivals"""

from dataclasses import dataclass
from typing import Self


@dataclass(kw_only=True)
class Arrival:
    """Class for keeping arrival data."""

    route: str
    trip: str
    time: float | None = None
    delay: float | None = None
    departure_time: float | None = None
    departure_delay: float | None = None
    stop_sequence: int | None = None

    def __lt__(self, other: Self) -> bool:
        if self.time is not None and other.time is not None:
            return self.time < other.time
        elif self.departure_time is not None and other.departure_time is not None:
            return self.departure_time < other.departure_time
        raise ValueError("Cannot compare items without arrival or departure times")

    def __gt__(self, other: Self) -> bool:
        if self.time is not None and other.time is not None:
            return self.time > other.time
        elif self.departure_time is not None and other.departure_time is not None:
            return self.departure_time > other.departure_time
        raise ValueError("Cannot compare items without arrival or departure times")

    def __eq__(self, other: Self) -> bool:
        if self.time is not None and other.time is not None:
            return self.time == other.time
        elif self.departure_time is not None and other.departure_time is not None:
            return self.departure_time == other.departure_time
        raise ValueError("Cannot compare items without arrival or departure times")
