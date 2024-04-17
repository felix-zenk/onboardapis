from __future__ import annotations

import logging

from datetime import datetime, timedelta
from typing import Generator

from ... import ConnectingTrain
from ....data import ThreadedRestAPI, ScheduledEvent, store, ID

logger = logging.getLogger(__name__)


class InouiConnector(ThreadedRestAPI):
    API_URL = "https://wifi.sncf/router/api"

    @store('gps')
    def gps(self) -> dict:
        return self.get("train/gps").json()

    @store('details')
    def details(self) -> dict:
        return self.get("train/details").json()

    def trainboard(self, station_id: ID) -> dict:
        return self.get(f"information/trainboard/{station_id}")

    def refresh(self) -> None:
        self.gps()
        self.details()

        # self._api["attendance"] = self.get("bar/attendance").json()
        # self._api["auto"] = self.get("connection/activate/auto").json()
        # self._api["catalog"] = self.get("food/catalog").json()
        # self._api["coverage"] = self.get("train/coverage").json()
        # self._api["graph"] = self.get("train/graph").json()
        # self._api["modules"] = self.get("configuration/modules").json()
        # self._api["poi"] = self.get("poi").json()
        # self._api["registry"] = self.get("connection/registry").json()
        # self._api["room"] = self.get("chat/room").json()
        # self._api["statistics"] = self.get("connection/statistics").json()
        # self._api["status"] = self.get("connection/status").json()
        # self._api["videos"] = self.get("media/videos").json()
        # self._api["wordings"] = self.get("media/wordings", params=dict(language="de")).json()

    def connections(self, station_id: ID) -> Generator[ConnectingTrain, None, None]:
        for connection in self.trainboard(station_id).get("train", []):
            yield ConnectingTrain(
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
