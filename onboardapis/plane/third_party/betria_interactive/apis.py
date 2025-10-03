from __future__ import annotations

from datetime import datetime, timedelta
from enum import ReprEnum

from .interfaces import FlightPath3DAPI
from ... import Plane, Airport
from ....data import Position, ScheduledEvent
from ....mixins import SpeedMixin, PositionMixin, StationsMixin
from ....units import meters_per_second, meters


class FlightPhase(str, ReprEnum):
    ASCENDING = 'Ascending'
    CRUISE = 'Cruise'
    DESCENDING = 'Descending'


class FlightPath3DPortal(Plane, SpeedMixin, PositionMixin, StationsMixin[Airport]):
    _api: FlightPath3DAPI

    @property
    def now(self) -> datetime:
        return datetime.fromtimestamp(self._api['last']['time'])

    @property
    def id(self) -> str:
        return self._api['last']['flightNumber']

    @property
    def speed(self) -> float:
        return meters_per_second(knots=self._api['last']['groundSpeedKnots'])

    @property
    def air_speed(self) -> float | None:
        return (
            meters_per_second(knots=self._api['last']['airSpeedKnots'])
            if 'airSpeedKnots' in self._api['last'] else None
        )

    @property
    def flight_phase(self) -> FlightPhase:
        return FlightPhase(self._api['last']['presentPhase'])

    @property
    def flight_revision(self) -> int:
        return self._api['last']['fltRev']

    @property
    def position(self) -> Position:
        return Position(
            latitude=self._api['last']['presentLat'],
            longitude=self._api['last']['presentLon'],
            altitude=meters(feet=self._api['last']['altitudeFeet']),
            heading=self._api['last']['trueHeading'],
            relative_roll=self._api['last']['roll'],
            relative_pitch=self._api['last']['pitch'],
        )

    @property
    def position_valid(self) -> bool:
        return self._api['last']['positionValid']

    @property
    def stations_dict(self) -> dict[str, Airport]:
        data = self._api['last']
        origin = Position(latitude=data['departureLat'], longitude=data['departureLon'])
        destination = Position(latitude=data['destinationLat'], longitude=data['destinationLon'])
        return {
            data['departureId']: Airport(
                id=data['departureId'],
                name=data['departBaggageId'],
                arrival=None,
                departure=(
                    ScheduledEvent(scheduled=self.now - timedelta(minutes=data['timeSinceTakeoff']))
                    if 'timeSinceTakeoff' in data else None
                ),
                position=origin,
                distance=0,
                _connections=(),
                gate=None,
            ),
            data['destinationId']: Airport(
                id=data['destinationId'],
                name=data['destBaggageId'],
                arrival=(
                    ScheduledEvent(scheduled=self.now - timedelta(minutes=data['timeToDestination']))
                    if 'timeToDestination' in data else None
                ),
                departure=None,
                position=destination,
                distance=destination.calculate_distance(origin),
                _connections=(),
                gate=None,
            ),
        }

    @property
    def current_station(self) -> Airport:
        return self.stations[0 if self.flight_phase == FlightPhase.ASCENDING else -1]
