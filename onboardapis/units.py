"""
Convert between different units
"""

from __future__ import annotations

from geopy.units import kilometers, meters, miles, feet, nautical, km, m, mi, ft, nm

__all__ = [
    'kilometers',
    'meters',
    'miles',
    'feet',
    'nautical',
    'km',
    'm',
    'mi',
    'ft',
    'nm',
    'seconds',
    'minutes',
    'hours',
    'coordinates_decimal_to_dms',
    'coordinates_dms_to_decimal',
    'kmh',
    'ms',
]


def coordinates_decimal_to_dms(
        coordinates: tuple[float, float]
) -> tuple[tuple[int, int, float], tuple[int, int, float]]:
    """
    Convert the tuple ``coordinates`` of coordinates to degrees, minutes, seconds

    :param coordinates: The decimal coordinates to convert to degrees, minutes, seconds
    :type coordinates: Tuple[float, float]
    :return: The coordinates in degrees, minutes, seconds
    :rtype: Tuple[Tuple[int, int, float], Tuple[int, int, float]]
    """
    lat, lon = coordinates
    lat_deg = int(abs(lat))
    lat_min = int((abs(lat) - lat_deg) * 60)
    lat_sec = ((abs(lat) - lat_deg) * 60 - lat_min) * 60
    lon_deg = int(abs(lon))
    lon_min = int((abs(lon) - lon_deg) * 60)
    lon_sec = ((abs(lon) - lon_deg) * 60 - lon_min) * 60
    return (-lat_deg if lat < 0 else lat_deg, lat_min, lat_sec), (
        -lon_deg if lon < 0 else lon_deg,
        lon_min,
        lon_sec,
    )


def coordinates_dms_to_decimal(
        coordinates: tuple[tuple[int, int, float], tuple[int, int, float]]
) -> tuple[float, float]:
    """
    Convert the tuple ``coordinates`` of degrees, minutes, seconds to decimal degrees

    :param coordinates: The degrees, minutes, seconds coordinates to convert to decimal degrees
    :type coordinates: Tuple[Tuple[int, int, float], Tuple[int, int, float]]
    :return: The coordinates in decimal degrees
    :rtype: Tuple[float, float]
    """
    (lat_deg, lat_min, lat_sec), (lon_deg, lon_min, lon_sec) = coordinates
    lat = lat_deg + lat_min / 60 + lat_sec / 3600
    lon = lon_deg + lon_min / 60 + lon_sec / 3600
    return lat, lon


# Convert between different units


def seconds(hours: float = 0, minutes: float = 0) -> float:  # noqa: F402
    """Convert to seconds"""
    ret = 0
    if hours:
        ret += hours * 3600
    if minutes:
        ret += minutes * 60
    return ret


def minutes(hours: float = 0, seconds: float = 0) -> float:  # noqa: F402
    """Convert to minutes"""
    ret = 0
    if hours:
        ret += hours * 60
    if seconds:
        ret += seconds / 60
    return ret


def hours(minutes: float = 0, seconds: float = 0) -> float:  # noqa: F402
    """Convert to hours"""
    ret = 0
    if minutes:
        ret += minutes / 60
    if seconds:
        ret += seconds / 3600
    return ret


def kmh(ms: float = None) -> float:  # noqa: F402
    """Convert to kilometers per hour"""
    ret = 0
    if ms:
        ret += kilometers(meters=ms) / hours(seconds=1)
    return ret


def ms(kmh: float = None) -> float:  # noqa: F402
    """Convert to meters per second"""
    ret = 0
    if kmh:
        ret += meters(kilometers=kmh) / seconds(hours=1)
    return ret
