from __future__ import annotations

import logging

from ....data import ThreadedRestAPI, store

logger = logging.getLogger(__name__)


class PortaleRegionaleConnector(ThreadedRestAPI):
    API_URL = 'https://www.portaleregionale.it/PortaleRegionale'

    @store('infovaggio')
    def infovaggio(self) -> dict:
        return self.get(
            "infoviaggio.getData.action",
            params={"stazioniList": True},
        ).json()

    @store('m53')
    def m53(self) -> dict:
        return self.get("m53.getData.action").json()

    @store('map')
    def map(self) -> dict:
        return self.get("map.getData.action").json()

    @store('meteo')
    def meteo(self) -> dict:
        return self.get("meteo.getData.action").json()

    @store('stations')
    def stations(self) -> dict:
        return self.get("stations.getData.action").json()

    @store('common')
    def common(self) -> dict:
        return self.get("common.getInfos.action").json()

    def refresh(self):
        self.infovaggio()
        # self.m53()
        # self.map()
        # self.meteo()
        # self.stations()
        # self.common()
