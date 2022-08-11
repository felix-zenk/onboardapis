import abc
import datetime
import time
from typing import Optional, Tuple, Dict, Union, Any, List, TypeVar, Generic, Callable

from ..exceptions import DataInvalidError
from ..utils.conversions import coordinates_to_distance
from ..utils.data import StaticDataConnector, DynamicDataConnector

T = TypeVar('T')


class ScheduledEvent(Generic[T]):
    """
    Something that is scheduled and can happen as ``scheduled``,
    but can also happen different from the expected and actually happens as ``actual``
    """

    __slots__ = ["scheduled", "actual"]

    def __init__(self, scheduled: Optional[T] = None, actual: Optional[T] = None):
        """
        Initialize a new :class:`ScheduledEvent`

        :param scheduled: The value that should happen
        :type scheduled: Optional[T]
        :param actual: The value that actually happens
        :type actual: Optional[T]
        """
        self.scheduled = scheduled
        self.actual = actual

    def __repr__(self):
        if self.actual is None:
            return f"<{self.__class__.__name__} {self.scheduled}>"
        return f"<{self.__class__.__name__} {self.actual}>"

    def __str__(self):
        if self.actual is None:
            return f"{self.scheduled}"
        return f"{self.actual}"


class Station(object):
    """
    A Station is a stop on the trip
    """

    __slots__ = [
        "__id", "__name", "__platform", "__arrival", "__departure", "__position", "__distance", "__connections"
    ]

    def __init__(self, station_id: Any, name: str, platform: ScheduledEvent[str] = None,
                 arrival: Optional[ScheduledEvent[datetime.datetime]] = None,
                 departure: Optional[ScheduledEvent[datetime.datetime]] = None, position: Tuple[float, float] = None,
                 distance: float = None, connections: Optional[Any] = None):
        """
        Initialize a new :class:`Station`

        :param station_id: The ID of the station
        :type station_id: Any
        :param name: The name of the station
        :type name: str
        :param platform: The platform that the vehicle is arriving at
        :type platform: Optional[ScheduledEvent[str]]
        :param arrival: The arrival time at this station
        :type arrival: Optional[ScheduledEvent[datetime.datetime]]
        :param departure: The departure time from this station
        :type departure: Optional[ScheduledEvent[datetime.datetime]]
        :param position: The geographic position of the station
        :type position: Tuple[float, float]
        :param distance: The distance from the start to this station
        :type distance: float
        :param connections: The connecting services departing from this station
        :type connections: Optional[Any]
        """
        self.__id = station_id
        self.__name = name
        self.__platform = platform
        self.__arrival = arrival
        self.__departure = departure
        self.__position = position
        self.__distance = distance
        self.__connections = connections

    @property
    def id(self) -> ...:
        """
        The unique ID of the station

        :return: The ID of the station
        :rtype: Any
        """
        return self.__id

    @property
    def name(self) -> str:
        """
        The name of the station

        :return: The name of the station
        :rtype: str
        """
        return self.__name

    @property
    def platform(self):
        return self.__platform

    @property
    def arrival(self):
        return self.__arrival

    @property
    def departure(self):
        return self.__departure

    @property
    def connections(self) -> Optional[List["ConnectingTrain"]]:
        return self.__connections

    @property
    def distance(self) -> float:
        return self.__distance

    @property
    def position(self) -> Tuple[float, float]:
        return self.__position

    def calculate_distance(self, other: Union["Station", Tuple[float, float], int, float]):
        """
        Calculate the distance in meters between this station and something else
        Accepts a :class:`Station`, a tuple of (latitude, longitude) or an integer for the distance calculation

        :param other: The other station or position to calculate the distance to
        """
        # Get the position of the other station or the distance of the other station from the start
        if isinstance(other, Station):
            other = (
                other.distance
                if other.distance is not None
                else (
                    other.position
                    if other.position is not None
                    else None
                )
            )
        # If there is not enough information to calculate the distance, return None
        if other is None:
            return None

        # Calculate the distance
        if isinstance(other, int) or isinstance(other, float):
            return self.distance - other if self.distance - other >= 0 else other - self.distance
        if isinstance(other, tuple):
            return coordinates_to_distance(self.position, other)
        return None


class Train(object, metaclass=abc.ABCMeta):
    """
    Interface specifying the attributes of a train
    """

    __slots__ = ["_static_data", "_dynamic_data"]

    def __init__(self):
        self._static_data: StaticDataConnector = ...
        self._dynamic_data: DynamicDataConnector = ...

    @abc.abstractmethod
    def init(self):
        self._static_data.refresh()
        self._dynamic_data.start()

    def now(self) -> datetime.datetime:
        """
        Get the current time from the train

        :return: The current time
        :rtype: datetime.datetime
        """
        return datetime.datetime.now()

    def calculate_distance(self, station: Station) -> float:
        return station.calculate_distance(self.distance or self.position)

    @property
    @abc.abstractmethod
    def id(self) -> str:
        """
        The unique ID of this specific train

        :return: The ID
        :rtype: str
        """
        pass

    @property
    @abc.abstractmethod
    def type(self) -> str:
        """
        The abbreviated train type

        :return: The train type
        :rtype: str
        """
        pass

    @property
    @abc.abstractmethod
    def number(self) -> str:
        """
        The line number of this train

        :return: The line number
        :rtype: str
        """
        pass

    @property
    @abc.abstractmethod
    def stations(self) -> Dict[Any, Station]:
        """
        The stations that this train passes through

        :return: The stations
        :rtype: Dict[str, Station]
        """
        pass

    @property
    @abc.abstractmethod
    def origin(self) -> Station:
        """
        The station where this train started the current journey

        :return: The first station on this trip
        :rtype: Station
        """
        stations = list(self.stations.values())
        if len(stations) > 0:
            return stations[0]
        raise DataInvalidError("No origin station found")

    @property
    @abc.abstractmethod
    def current_station(self) -> Station:
        """
        The station where this train will arrive next or is currently at

        :return: The current station
        :rtype: Station
        """
        # Get the current station id
        # Get the station from the stations dict
        pass

    @property
    @abc.abstractmethod
    def destination(self) -> Station:
        """
        The station where this train will end the current journey

        :return: The last station on this trip
        :rtype: Station
        """
        stations = list(self.stations.values())
        if len(stations) > 0:
            return stations[-1]
        raise DataInvalidError("No destination station found")

    @property
    @abc.abstractmethod
    def speed(self) -> float:
        """
        The current speed of the train in meters / second

        :return: The speed of the train
        :rtype: float
        """
        pass

    @property
    @abc.abstractmethod
    def distance(self) -> float:
        """
        The distance from the start in meters

        :return: The distance
        :rtype: float
        """
        pass

    @property
    @abc.abstractmethod
    def position(self) -> Tuple[float, float]:
        """
        The current position of the train as a tuple of latitude and longitude

        :return: The position of the train
        :rtype: Tuple[float, float]
        """
        pass

    @property
    @abc.abstractmethod
    def delay(self) -> float:
        """
        The current delay of the train in seconds

        :return: The delay of the train
        :rtype: float
        """
        pass


class ConnectingTrain(object):
    """
    A connecting train is a train that is not part of the main trip but of a connecting service

    It may only have limited information available
    """

    __slots__ = ["train_type", "line_number", "platform", "destination", "departure"]

    def __init__(self, train_type: str = None, line_number: str = None, platform: ScheduledEvent[str] = None,
                 destination: str = None, departure: ScheduledEvent[datetime.datetime] = None):
        self.train_type = train_type
        self.line_number = line_number
        self.platform = platform
        self.destination = destination
        self.departure = departure

    def __str__(self):
        return f"{self.train_type}{self.line_number} to {self.destination} ({self.departure}, platform {self.platform})"

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.train_type}{self.line_number} " \
               f"-> {self.destination} ({repr(self.departure)}, {repr(self.platform)})>"


class _LazyStation(Station):
    """
    The LazyStation is a Station that maybe does not yet have information on connecting trains.
    If it does not have information by the time it is requested by the user,
    it will then proceed to load the information through ``lazy_func``.
    """

    __slots__ = ["_lazy_func", "_cache_valid_until", "_cache_timeout"]

    def __init__(self, *args, lazy_func: Optional[Callable[..., List[ConnectingTrain]]] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._lazy_func = lazy_func
        self._cache_valid_until = 0
        self._cache_timeout = 60

    __init__.__doc__ = Station.__init__.__doc__

    @property
    def connections(self) -> Optional[List[ConnectingTrain]]:
        def request_data():
            connections = self._lazy_func()
            self.__connections = connections
            self._cache_valid_until = time.time() + self._cache_timeout  # Cache this result for the next minute
            return connections

        if self._lazy_func is None:
            return self.__connections  # None or connections

        # Lazy func is not None
        # Connections may be None or not
        if time.time() > self._cache_valid_until:
            return request_data()
        # Cache time is valid
        # If there is no cache yet, request the data
        if self.__connections is None:
            return request_data()
        # Return cached connections
        return self.__connections
