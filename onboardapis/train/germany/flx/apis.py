from ...mixins import PositionMixin, SpeedMixin
from ...data import JSONDataConnector, DynamicDataConnector, Position
from .. import Train, IncompleteTrainMixin


class FlixTainment(Train, PositionMixin, SpeedMixin, IncompleteTrainMixin):
    """
    Wrapper for interacting with the Flixtrain FLIXTainment API
    (few methods are available, because the API is very sparse)
    """

    def __init__(self):
        super().__init__()
        self._dynamic_data = _FlixTainmentDynamicConnector()

    def position(self) -> Position:
        return Position(
            latitude=self._dynamic_data.load("position", {}).get("latitude", None),
            longitude=self._dynamic_data.load("position", {}).get("longitude", None),
        )

    def speed(self) -> float:
        return float(self._dynamic_data.load("position", {}).get("speed", 0.0))

    # No more information available
