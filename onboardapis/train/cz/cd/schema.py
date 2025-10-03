from __future__ import annotations

import logging

from typing import TypedDict, Annotated

from annotated_types import MaxLen, Len, Ge, Le

logger = logging.getLogger(__name__)


class CdObpConnectivitySchema(TypedDict):
    online: bool


class CdObpInfoSchema(TypedDict):
    id: Annotated[str, MaxLen(3)]
    deviceId: Annotated[str, Len(12)]
    name: str
    group: str  # "ComfortJet"
    connexionId: int
    gpsLat: float
    gpsLng: float
    speed: int
    altitude: int


class CdObpUserDataUsageSchema(TypedDict):
    used: Annotated[int, Ge(0)]
    limit: Annotated[int, Ge(0)]
    expire: None
    dataLimit: Annotated[int, Ge(0)]
    speedLimit: bool
    region: None


class CdObpUserSchema(TypedDict):
    id: str  # UUID "XXXXXX-XXXXXX-XXXXXX-XXXXXX-XXXXXX-XXXXXX-XXXX"
    ip: None  # | str?
    mac: str  # "XX:XX:XX:XX:XX:XX"
    authenticated: Annotated[int, Ge(0), Le(1)]
    category: str  # "authorized"
    dataUsage: CdObpUserDataUsageSchema


class CdObpRealtimeSchema(TypedDict):
    gpsLat: float
    gpsLng: float
    prevGpsLat: float
    prevGpsLng: float
    speed: Annotated[int, Ge(0)]
    delay: Annotated[int, Ge(0)]
    altitude: Annotated[int, Ge(0)]
    temperature: None


class CdObpCurrentSchema(TypedDict):
    id: None
    name: None
    line: None
    connexionTimes: list
