"""Stop Times Dataset."""

import os
from dataclasses import dataclass
from enum import Enum
from typing import Self

from .helpers import get_as_number
from .static_dataset import GtfsStaticDataset


class PickupType(Enum):
    """
    Pickup Type.
    see https://gtfs.org/documentation/schedule/reference/#stop_timestxt
    """

    REGULARLY_SCHEDULED = 0
    NO_PICKUP_AVAILABLE = 1
    PHONE_AGENCY_FOR_PICKUP = 2
    COORDINATE_WITH_DRIVER_FOR_PICKUP = 3


class DropOffType(Enum):
    """
    Drop-Off Type.
    see https://gtfs.org/documentation/schedule/reference/#stop_timestxt
    """

    REGULARLY_SCHEDULED = 0
    NO_DROP_OFF_AVAILABLE = 1
    PHONE_AGENCY_FOR_DROP_OFF = 2
    COORDINATE_WITH_DRIVER_FOR_DROP_OFF = 3


class TimePoint(Enum):
    """
    Timepoint
    see https://gtfs.org/documentation/schedule/reference/#stop_timestxt
    """

    APPROXIMATE = 0
    EXACT = 1


@dataclass(order=True)
class GtfsArrivalDepartureTime:
    """GTFS Specific Arrival or Departure Times from stoptimes.txt"""

    hour: int
    minute: int
    second: int

    @staticmethod
    def strptime(time_str: str) -> Self:
        """
        Generate the dataclass from a string in a dataset row.
        Times are permitted to exceed 24 hours for datasets after midnight, so the
        built-in method datetime.strptime cannot be used.
        see https://gtfs.org/documentation/schedule/reference/#stop_timestxt
        arrival_time and departure_time
        """
        return GtfsArrivalDepartureTime(*[int(x) for x in time_str.split(":")])


@dataclass
class StopTime:
    """Stop Time."""

    def __init__(self, stop_times_data_dict: dict) -> None:
        self.trip_id = stop_times_data_dict["trip_id"]

        self.arrival_time: GtfsArrivalDepartureTime | None = None
        if (arrival_time_str := stop_times_data_dict.get("arrival_time")) is not None:
            self.arrival_time = GtfsArrivalDepartureTime.strptime(arrival_time_str)

        self.departure_time: GtfsArrivalDepartureTime | None = None
        if (
            departure_time_str := stop_times_data_dict.get("departure_time")
        ) is not None:
            self.departure_time = GtfsArrivalDepartureTime.strptime(departure_time_str)

        self.stop_id = stop_times_data_dict.get("stop_id")
        self.location_group_id = stop_times_data_dict.get("location_group_id")
        self.location_id = stop_times_data_dict.get("location_id")

        self.stop_sequence = int(stop_times_data_dict["stop_sequence"])
        self.stop_headsign = stop_times_data_dict.get("stop_headsign", "")
        self.start_pickup_drop_off_window = stop_times_data_dict.get(
            "start_pickup_drop_off_window"
        )
        self.end_pickup_drop_off_window = stop_times_data_dict.get(
            "end_pickup_drop_off_window"
        )
        self.pickup_type = PickupType(
            get_as_number(stop_times_data_dict, "pickup_type", int)
        )
        self.drop_off_type = DropOffType(
            get_as_number(stop_times_data_dict, "drop_off_type", int)
        )

        self.continuous_pickup = PickupType(
            get_as_number(stop_times_data_dict, "continuous_pickup", int)
        )

        self.continuous_drop_off = DropOffType(
            get_as_number(stop_times_data_dict, "continuous_drop_off", int)
        )

        self.shape_dist_traveled = float(
            get_as_number(stop_times_data_dict, "shape_dist_traveled", float)
        )
        self.timepoint = TimePoint(
            get_as_number(stop_times_data_dict, "timepoint", int, 1)
        )


@dataclass
class StopTimesDataset(GtfsStaticDataset):
    """Dataset for Stop Times."""

    stop_times: dict[str, dict[int, StopTime]]

    def __init__(self, *gtfs_files: os.PathLike, **kwargs):
        self.stop_times = {}
        super().__init__(*gtfs_files, **kwargs)

    def add_gtfs_data(self, zip_filelike) -> None:
        for line in self._get_gtfs_record_iter(zip_filelike, "stop_times.txt"):
            stop_time = StopTime(line)
            self.stop_times.setdefault(stop_time.trip_id, {})[
                stop_time.stop_sequence
            ] = stop_time

    def get(self, trip_id, stop_sequence, *, default: StopTime | None = None):
        """Get Stop Time from Dataset."""
        by_trip_id = self.stop_times.get(trip_id)
        if by_trip_id is not None:
            return by_trip_id.get(stop_sequence, default)
        return default
