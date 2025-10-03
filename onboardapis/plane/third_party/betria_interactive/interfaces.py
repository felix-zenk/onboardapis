from __future__ import annotations

import time

from typing import ClassVar

from ....data import ThreadedRestAPI, store


class FlightPath3DAPI(ThreadedRestAPI):
    API_URL: ClassVar[str]  # Has to be provided by subclasses!

    @store('last')
    def last(self) -> dict:
        return self.get('/fp3d_logs/last', params={'_': int(time.time() * 1000)}).json()

    def refresh(self) -> None:
        self.last()


# class FlightPath3DDemoAPI(FlightPath3DAPI):
#     API_URL = 'https://inflight.betria.com'


# class FlightPath3DWebsocketAPI(): ...
