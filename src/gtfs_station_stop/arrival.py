"""Dataclass for Arrivals"""

from dataclasses import dataclass
from datetime import datetime
from typing import Self

from gtfs_station_stop.vehicle import Vehicle


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
    current_station: str | None = None
    destination: str | None = None
    vehicle: Vehicle | None = None

    def __post_init__(self):
        if isinstance(self.time, datetime):
            self.time = self.time.timestamp()
        if isinstance(self.departure_time, datetime):
            self.departure_time = self.departure_time.timestamp()

    def _comparison_value(self) -> float | None:
        if self.time is not None:
            return self.time
        if self.departure_time is not None:
            return self.departure_time
        if self.delay is not None:
            return float(self.delay)
        if self.departure_delay is not None:
            return float(self.departure_delay)
        return None

    def __lt__(self, other: Self) -> bool:
        self_value = self._comparison_value()
        other_value = other._comparison_value()
        if self_value is not None and other_value is not None:
            return self_value < other_value
        raise ValueError(
            "Cannot compare items without arrival, departure, or delay values"
        )

    def __gt__(self, other: Self) -> bool:
        self_value = self._comparison_value()
        other_value = other._comparison_value()
        if self_value is not None and other_value is not None:
            return self_value > other_value
        raise ValueError(
            "Cannot compare items without arrival, departure, or delay values"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Arrival):
            return NotImplemented
        self_value = self._comparison_value()
        other_value = other._comparison_value()
        if self_value is not None and other_value is not None:
            return self_value == other_value
        raise ValueError(
            "Cannot compare items without arrival, departure, or delay values"
        )
