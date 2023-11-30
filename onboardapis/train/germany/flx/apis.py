from ....units import ms
from ....data import Position
from ... import Train, IncompleteTrainMixin
from .connectors import FlixTainmentConnector


class FlixTainment(IncompleteTrainMixin, Train):
    """
    Wrapper for interacting with the Flixtrain FLIXTainment API
    (few methods are available, because the API is very sparse)
    """

    _data: FlixTainmentConnector

    def __init__(self):
        self._data = FlixTainmentConnector()
        super().__init__()

    @property
    def position(self) -> Position:
        return Position(
            latitude=self._data["position"].get("latitude", None),
            longitude=self._data["position"].get("longitude", None),
        )

    @property
    def speed(self) -> float:
        return ms(kmh=float(self._data["position"].get("speed", 0.0)))

    # No more information available
