"""
Implementation for the french train operator SNCF.

TODO Not tested yet.
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Generator

from requests import HTTPError

from ...types import ID
from ...mixins import StationsMixin
from .. import Train, TrainStation, ConnectingTrain
from data import (
    StaticDataConnector,
    JSONDataConnector,
    DynamicDataConnector,
    Position,
    ScheduledEvent,
)


# socket.io at /socket.io/


class _InouiStaticConnector(JSONDataConnector, StaticDataConnector):
    API_URL = "wifi.sncf"

    def refresh(self):
        pass


class _InouiDynamicConnector(JSONDataConnector, DynamicDataConnector):
    API_URL = "wifi.sncf"

    def refresh(self):
        self._cache.store("gps", self._get("/router/api/train/gps"))
        self._cache.store("details", self._get("/router/api/train/details"))
        # self._cache.store("attendance", self._get("/router/api/bar/attendance"))
        # self._cache.store("auto", self._get("/router/api/connection/activate/auto"))
        # self._cache.store("catalog", self._get("/router/api/food/catalog"))
        # self._cache.store("coverage", self._get("/router/api/train/coverage"))
        # self._cache.store("graph", self._get("/router/api/train/graph"))
        # self._cache.store("modules", self._get("/router/api/configuration/modules"))
        # self._cache.store("poi", self._get("/router/api/poi"))
        # self._cache.store("registry", self._get("/router/api/connection/registry"))
        # self._cache.store("room", self._get("/router/api/chat/room"))
        # self._cache.store("statistics", self._get("/router/api/connection/statistics"))
        # self._cache.store("status", self._get("/router/api/connection/status"))
        # self._cache.store("videos", self._get("/router/api/media/videos"))
        # self._cache.store("wordings", self._get("/router/api/media/wordings?language=de"))

    def connections(self, station_id: ID) -> Generator[ConnectingTrain, None, None]:
        try:
            yield from (
                ConnectingTrain(
                    vehicle_type=connection.get("type"),
                    line_number=connection.get("num"),
                    departure=ScheduledEvent(
                        scheduled=datetime.fromisoformat(connection.get("heure")),
                        actual=datetime.fromisoformat(connection.get("heure"))
                        + timedelta(minutes=int(connection.get("retard", 0))),
                    ),
                    destination=connection.get("origdest"),
                    platform=ScheduledEvent(
                        scheduled=connection.get("attribut_voie"),
                        actual=connection.get("attribut_voie"),
                    ),
                )
                for connection in self._get(
                    f"/router/api/information/trainboard/{station_id}"
                ).get("train", [])
            )
        except HTTPError:
            return


class PortalINOUI(Train, StationsMixin):
    _static_data = _InouiStaticConnector()
    _dynamic_data = _InouiDynamicConnector()

    @property
    def id(self) -> str:
        return self._dynamic_data.load("details").get("trainId")

    @property
    def type(self) -> str:
        return self._dynamic_data.load("details").get(
            "carrier"
        )  # todo carrier != type?

    @property
    def number(self) -> str:
        return self._dynamic_data.load("details").get("number")

    @property
    def stations_dict(self) -> Dict[Any, TrainStation]:
        return {
            stop.get("code"): TrainStation(
                station_id=stop.get("code"),
                name=stop.get("label"),
                platform=ScheduledEvent(scheduled=None, actual=None),
                arrival=ScheduledEvent(
                    scheduled=datetime.fromisoformat(stop.get("theoricDate")),
                    actual=datetime.fromisoformat(stop.get("realDate")),
                ),
                departure=ScheduledEvent(
                    scheduled=datetime.fromisoformat(stop.get("theoricDate"))
                    + timedelta(minutes=int(stop.get("duration", 0))),
                    actual=datetime.fromisoformat(stop.get("realDate"))
                    + timedelta(minutes=int(stop.get("duration", 0))),
                ),
                position=Position(
                    latitude=int(stop.get("coordinates", {}).get("latitude", 0)),
                    longitude=int(stop.get("coordinates", {}).get("longitude", 0)),
                ),
                distance=float(stop.get("progress", {}).get("remainingDistance", 0)),
                connections=self._dynamic_data.connections(station_id=stop.get("code")),
            )
            for stop in self._dynamic_data.load("details").get("stops", [])
        }

    @property
    def current_station(self) -> TrainStation:
        current_station_id, *_ = (
            stop.get("code")
            for stop
            in self._dynamic_data.load("details").get("stops", [])
            if 0 < int(stop.get("progress", {}).get('progressPercentage', 0)) < 100
        )
        return self.stations_dict.get(current_station_id)

    @property
    def speed(self) -> float:
        return float(self._dynamic_data.load("gps").get("speed"))

    @property
    def distance(self) -> float:
        return sum(
            float(stop.get('progress', {}).get('traveledDistance', 0))
            for stop
            in self._dynamic_data.load('details').get('stops', []),
        )

    @property
    def position(self) -> Position:
        gps = self._dynamic_data.load("gps")
        return Position(
            latitude=float(gps.get("latitude", 0)),
            longitude=float(gps.get("longitude", 0)),
            altitude=float(gps.get("altitude", 0)),
            bearing=float(gps.get("heading", 0)),
        )
