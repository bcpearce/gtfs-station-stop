import os
from dataclasses import dataclass
from enum import Enum
from typing import Any

from gtfs_station_stop.static_dataset import GtfsStaticDataset


class RouteType(Enum):
    UNKNOWN = -1

    TRAM = 0
    SUBWAY = 1
    RAIL = 2
    BUS = 3
    FERRY = 4
    CABLE_TRAM = 5
    AERIAL_LIFT = 6
    FUNICULAR = 7
    TROLLEYBUS = 11

    RAILWAY_SERVICE = 100
    HIGH_SPEED_RAIL_SERVICE = 101
    LONG_DISTANCE_TRAIN = 102
    INTER_REGIONAL_RAIL_SERVICE = 103
    CAR_TRANSPORT_RAIL_SERVICE = 104
    SLEEPER_RAIL_SERVICE = 105
    REGIONAL_RAIL_SERVICE = 106
    TOURIST_RAIL_SERVICE = 107
    RAIL_SHUTTLE_WITHIN_COMPLEX = 108
    SUBURBAN_RAILWAY = 109
    REPLACEMENT_RAIL_SERVICE = 110
    SPECIAL_RAIL_SERVICE = 111
    LORRY_TRANSPORT_RAIL = 112

    BUS_SERVICE = 700
    REGIONAL_BUS_SERVICE = 701
    EXPRESS_BUS_SERVICE = 702
    STOPPING_BUS_SERVICE = 703
    LOCAL_BUS_SERVICE = 704
    NIGHT_BUS_SERVICE = 705
    POST_BUS_SERVICE = 706
    SPECIAL_NEEDS_BUS = 707
    MOBILITY_BUS_SERVICE = 708
    MOBILITY_BUS_FOR_REGISTERED_DISABLED = 709
    SIGHTSEEING_BUS = 710
    SHUTTLE_BUS = 711
    SCHOOL_BUS = 712
    SCHOOL_AND_PUBLIC_SERVICE_BUS = 713
    RAIL_REPLACEMENT_BUS_SERVICE = 714
    DEMAND_AND_RESPONSE_BUS_SERVICE = 715
    ALL_BUS_SERVICES = 716

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            value = int(value)
            for member in cls:
                if member.value == value:
                    return member
        return cls.UNKNOWN

    def pretty_name(self):
        PRETTY_NAMES = {
            RouteType.TRAM: "Tram",
            RouteType.SUBWAY: "Subway",
            RouteType.RAIL: "Rail",
            RouteType.BUS: "Bus",
            RouteType.FERRY: "Ferry",
            RouteType.CABLE_TRAM: "Cable Tram",
            RouteType.AERIAL_LIFT: "Aerial Lift",
            RouteType.FUNICULAR: "Funicular",
            RouteType.TROLLEYBUS: "Trolleybus",
            RouteType.SHUTTLE_BUS: "Shuttle Bus",
        }
        return PRETTY_NAMES.get(self) or self.name


class RouteInfo:
    def __init__(self, route_data_dict: dict):
        self.agency_id = route_data_dict.get("agency_id")
        self.id = route_data_dict["route_id"]
        self.short_name = route_data_dict.get("route_short_name")
        self.long_name = route_data_dict.get("route_long_name")
        if self.short_name is None and self.long_name is None:
            raise ValueError(
                "Either 'route_short_name' or 'route_long_name' must be provided."
            )
        self.type = RouteType(int(route_data_dict["route_type"]))
        self.desc = route_data_dict.get("route_desc")
        self.url = route_data_dict.get("route_url")
        self.color = route_data_dict.get("route_color")
        self.text_color = route_data_dict.get("route_text_color")


@dataclass
class RouteInfoDataset(GtfsStaticDataset):
    route_infos: dict[str, RouteInfo]

    def __init__(self, *gtfs_files: os.PathLike, **kwargs):
        self.route_infos = {}
        super().__init__(*gtfs_files, **kwargs)

    def add_gtfs_data(self, zip_filelike: os.PathLike):
        for line in self._get_gtfs_record_iter(zip_filelike, "routes.txt"):
            id = line["route_id"]
            self.route_infos[id] = RouteInfo(line)

    def get_routes(self):
        return self.route_infos.keys()

    def __getitem__(self, key):
        return self.route_infos[key]

    def get(self, key: str | None, default: Any | None = None):
        return self.route_infos.get(key, default)
