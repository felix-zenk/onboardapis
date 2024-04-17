from __future__ import annotations

import logging

from ....data import ThreadedRestAPI, store

logger = logging.getLogger(__name__)


class FlixTainmentAPI(ThreadedRestAPI):
    API_URL = "https://media.flixtrain.com"

    @store('position')
    def position(self) -> dict:
        return self.get("services/pis/v1/position")

    def refresh(self) -> None:
        self.position()
