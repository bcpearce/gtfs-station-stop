import os
from collections.abc import Iterable

from gtfs_station_stop.helpers import gtfs_record_iter


class TripInfo:
    def __init__(self, trip_data_dict: dict):
        self.route_id = trip_data_dict["route_id"]
        self.trip_id = trip_data_dict["trip_id"]
        self.service_id = trip_data_dict["service_id"]
        self.trip_headsign = trip_data_dict["trip_headsign"]
        self.direction_id = trip_data_dict["direction_id"]
        self.shape_id = trip_data_dict["shape_id"]

    def __repr__(self):
        return f"{self.trip_id}: {self.route_id} to {self.trip_headsign}"


class TripInfoDatabase:
    def __init__(self, gtfs_files: Iterable[os.PathLike] | os.PathLike | None = None):
        self._trip_infos = {}
        if gtfs_files is not None:
            if isinstance(gtfs_files, os.PathLike):
                gtfs_files = [gtfs_files]
            for file in gtfs_files:
                self.add_gtfs_data(file)

    def add_gtfs_data(self, zip_filepath: os.PathLike):
        for line in gtfs_record_iter(zip_filepath, "trips.txt"):
            id = line["trip_id"]
            self._trip_infos[id] = TripInfo(line)

    def get_close_match(self, key) -> TripInfo | None:
        """Gets the first close match for a given trip ID, to use with realtime data"""
        return next(
            (
                trip_info
                for trip_id, trip_info in self._trip_infos.items()
                if key in trip_id
            ),
            None,
        )

    def __getitem__(self, key) -> TripInfo:
        return self._trip_infos[key]
