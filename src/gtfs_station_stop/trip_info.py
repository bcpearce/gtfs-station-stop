import csv
import os
from collections.abc import Iterable
from io import StringIO
from zipfile import ZipFile


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

    def add_gtfs_data(self, filepath: os.PathLike):
        with ZipFile(filepath) as zip:
            # Find the trips.txt file
            first_or_none: str = next(
                (name for name in zip.namelist() if name == "trips.txt"), None
            )
            if first_or_none is None:
                raise RuntimeError("Did not find required trips.txt file")
            with StringIO(
                str(zip.read(first_or_none), encoding="ASCII")
            ) as stops_dot_txt:
                reader = csv.DictReader(
                    stops_dot_txt,
                    delimiter=",",
                )
                for line in reader:
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
