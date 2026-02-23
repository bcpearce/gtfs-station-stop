"""Representation of a Vehicle from vehicle positions update"""

from dataclasses import dataclass

from google.transit import gtfs_realtime_pb2


@dataclass(kw_only=True)
class Vehicle:
    """Vehicle Position Data"""

    trip_id: str
    route_id: str | None = None
    timestamp: int | None = None
    latitude: float | None = None
    longitude: float | None = None
    bearing: float | None = None


def from_vehicle_position_message(
    feed_entity: gtfs_realtime_pb2.FeedEntity,
) -> Vehicle:
    """Create from Feed Message"""
    return Vehicle(
        trip_id=feed_entity.trip.trip_id,
        route_id=feed_entity.trip.route_id,
        timestamp=feed_entity.timestamp,
        latitude=feed_entity.position.latitude,
        longitude=feed_entity.position.longitude,
        bearing=feed_entity.position.bearing,
    )
