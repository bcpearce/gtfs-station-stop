import csv
import os
from collections.abc import Iterable
from io import StringIO
from zipfile import ZipFile


class StationStopInfo:
    pass


class StationStopInfo:
    def __init__(self, parent: StationStopInfo, station_data_dict: dict):
        self.id = station_data_dict["stop_id"]
        self.name = station_data_dict["stop_name"]
        self.lat = station_data_dict.get("stop_lat")
        self.lon = station_data_dict.get("stop_lon")
        self.parent = parent

    def __repr__(self):
        return f"{self.id}: {self.name}, lat: {self.lat}, long: {self.lon}, parent: {self.parent.id}"


class StationStopInfoDatabase:
    def __init__(self, gtfs_files: Iterable[os.PathLike] | os.PathLike | None = None):
        self._station_stop_infos = {}
        if gtfs_files is not None:
            if isinstance(gtfs_files, os.PathLike):
                gtfs_files = [gtfs_files]
            for file in gtfs_files:
                self.add_gtfs_data(file)

    def add_gtfs_data(self, filepath: os.PathLike):
        with ZipFile(filepath) as zip:
            # Find the stops.txt file
            first_or_none: str = next(
                (name for name in zip.namelist() if name == "stops.txt"), None
            )
            if first_or_none is None:
                raise RuntimeError("Did not find required stops.txt file")
            # Create the dictionary of IDs, parents should preceed the children
            with StringIO(
                str(zip.read(first_or_none), encoding="ASCII")
            ) as stops_dot_txt:
                reader = csv.DictReader(
                    stops_dot_txt,
                    delimiter=",",
                )
                for line in reader:
                    id = line["stop_id"]
                    parent = self._station_stop_infos.get(line["parent_station"])
                    self._station_stop_infos[id] = StationStopInfo(parent, line)

    def __getitem__(self, key) -> StationStopInfo:
        return self._station_stop_infos[key]
