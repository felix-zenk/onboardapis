from __future__ import annotations

import logging

from datetime import datetime, timedelta
from typing import Dict, Any

from ....data import (
    Position,
    ScheduledEvent,
)
from ... import Train, TrainStation
from .interfaces import InouiConnector

logger = logging.getLogger(__name__)


class PortalINOUI(Train):
    _api: InouiConnector

    def __init__(self):
        self._api = InouiConnector()
        Train.__init__(self)

    @property
    def id(self) -> str:
        return self._api["details"].get("trainId")

    @property
    def type(self) -> str:
        return self._api["details"].get(
            "carrier"
        )  # todo carrier != type?

    @property
    def line_number(self) -> str:
        return self._api["details"].get("number")

    @property
    def stations_dict(self) -> Dict[Any, TrainStation]:
        return {
            stop.get("code"): TrainStation(
                id=stop.get("code"),
                name=stop.get("label"),
                platform=None,
                arrival=ScheduledEvent(
                    scheduled=datetime.fromisoformat(stop.get("theoricDate")),
                    actual=datetime.fromisoformat(stop.get("realDate")),
                ),
                departure=ScheduledEvent(
                    scheduled=(
                        datetime.fromisoformat(stop.get("theoricDate"))
                        + timedelta(minutes=int(stop.get("duration", 0)))
                    ),
                    actual=(
                        datetime.fromisoformat(stop.get("realDate"))
                        + timedelta(minutes=int(stop.get("duration", 0)))
                    ),
                ),
                position=Position(
                    latitude=int(stop.get("coordinates", {}).get("latitude", 0)),
                    longitude=int(stop.get("coordinates", {}).get("longitude", 0)),
                ),
                distance=float(stop.get("progress", {}).get("remainingDistance", 0)),
                _connections=self._api.connections(station_id=stop.get("code")),
            )
            for stop in self._api["details"].get("stops", [])
        }

    @property
    def current_station(self) -> TrainStation:
        current_station_id, *_ = (
            stop.get("code")
            for stop
            in self._api["details"].get("stops", [])
            if 0 < int(stop.get("progress", {}).get('progressPercentage', 0)) < 100
        )
        return self.stations_dict.get(current_station_id)

    @property
    def speed(self) -> float:
        return float(self._api["gps"].get("speed"))

    @property
    def distance(self) -> float:
        return sum(
            float(stop.get('progress', {}).get('traveledDistance', 0))
            for stop
            in self._api['details'].get('stops', [])
        )

    @property
    def position(self) -> Position:
        gps = self._api["gps"]
        return Position(
            latitude=float(gps.get("latitude", 0)),
            longitude=float(gps.get("longitude", 0)),
            altitude=float(gps.get("altitude", 0)),
            heading=float(gps.get("heading", 0)),
        )
