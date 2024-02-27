from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from functools import wraps
from threading import Thread
from types import MethodType
from typing import Optional, Any, TypeVar, Generic, ClassVar, Callable, Union

from geopy import Point
from restfly import APISession

def default(arg: Any, __default: Any = None, *, bool: bool = True) -> Any: ...

T = TypeVar('T')
T_return = TypeVar('T_return')

class ScheduledEvent(Generic[T]):
    scheduled: T
    actual: T
    def __init__(self, scheduled: T, actual: Optional[T] = None) -> None: ...

@dataclass
class Position(object):
    latitude: float
    longitude: float
    altitude: Optional[float] = None
    heading: Optional[float] = None
    def __getitem__(self, item: int) -> float: ...
    def calculate_distance(self, other: Position) -> float: ...
    def to_point(self, altitude: bool = False) -> Point: ...

class DataConnector(metaclass=ABCMeta):
    API_URL: ClassVar[str]
    _data: dict
    def load(self, key: str, __default: Any = None) -> Any: ...
    def store(self, key: str, value: Any) -> None: ...
    def __getitem__(self, item: str) -> Any: ...
    def __setitem__(self, key: str, value: Any) -> None: ...

class ThreadedDataConnector(DataConnector, Thread):
    _connected: bool
    _running: bool
    @property
    def connected(self) -> bool: ...
    def _run(self) -> None: ...
    def stop(self) -> None: ...
    def reset(self) -> None: ...
    @abstractmethod
    def refresh(self) -> None: ...

class BlockingRESTDataConnector(APISession, DataConnector):
    def __init__(self, **kwargs: Any) -> None: ...
    def _build_session(self, **kwargs) -> None: ...

class ThreadedRESTDataConnector(ThreadedDataConnector, BlockingRESTDataConnector, metaclass=ABCMeta):
    def __init__(self, **kwargs: Any) -> None: ...

"""
# Unused
class GraphQLDataConnector(DataConnector, metaclass=ABCMeta): ...
class WebsocketDataConnector(DataConnector, metaclass=ABCMeta): ...
class SocketIODataConnector(DataConnector, metaclass=ABCMeta): ...
"""

class DummyDataConnector(DataConnector):
    API_URL: ClassVar[str]
    def load(self, key: str, __default: Any = None) -> Any: ...

def store(name: str | MethodType) -> Union[
    Callable[[MethodType], Callable[[DataConnector, tuple[Any, ...], dict[str, Any]], T_return]],
    Callable[[DataConnector, tuple[Any, ...], dict[str, Any]], T_return]
]:
    def decorator(method: Callable[[DataConnector, tuple, dict], T_return]) -> Callable[
        [DataConnector, tuple[Any, ...], dict[str, Any]],
        T_return
    ]:
        @wraps(method)
        def wrapper(self: DataConnector, *args: Any, **kwargs: Any) -> T_return: ...

class InternetAccessInterface(metaclass=ABCMeta):
    _is_enabled: bool
    @abstractmethod
    def enable(self) -> None: ...
    @abstractmethod
    def disable(self) -> None: ...
    @property
    def is_enabled(self) -> bool: ...

class InternetMetricsInterface(metaclass=ABCMeta):
    @abstractmethod
    def limit(self) -> float | None: ...
