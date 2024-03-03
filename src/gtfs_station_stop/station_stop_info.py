import os
from collections.abc import Iterable

from gtfs_station_stop.helpers import gtfs_record_iter


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

    def add_gtfs_data(self, zip_filepath: os.PathLike):
        for line in gtfs_record_iter(zip_filepath, "stops.txt"):
            id = line["stop_id"]
            parent = self._station_stop_infos.get(line["parent_station"])
            self._station_stop_infos[id] = StationStopInfo(parent, line)

    def __getitem__(self, key) -> StationStopInfo:
        return self._station_stop_infos[key]
