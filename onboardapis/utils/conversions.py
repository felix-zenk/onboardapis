"""
Convert between different units
"""

from typing import Tuple


def coordinates_to_distance(start: Tuple[float, float], end: Tuple[float, float]) -> float:
    """
    Convert the two tuples ``start`` and ``end`` of coordinates
    into the ``distance`` in meters that lies between those two positions

    Currently not implemented!

    :param start: The start coordinates
    :type start: Tuple[float, float]
    :param end: The end coordinates
    :type end: Tuple[float, float]
    :return: The distance in meters between 'start' and 'end'
    :rtype: float
    """
    raise NotImplementedError()


# Convert between different units

def ms_to_kmh(meters_per_second: float) -> float:
    """
    Convert meters/second into kilometers/hour

    :param meters_per_second: The value in meters/second
    :type meters_per_second: float
    :return: The result in kilometers/hour
    :rtype: float
    """
    return meters_per_second * 3.6


def kmh_to_ms(kilometers_per_hour: float) -> float:
    """
    Convert kilometers/hour into meters/second

    :param kilometers_per_hour: The value in kilometers/hour
    :type kilometers_per_hour: float
    :return: The result in meters/second
    :rtype: float
    """
    return kilometers_per_hour / 3.6


def ms_to_mph(meters_per_second) -> float:
    """
    Convert meters/second into miles/hour

    :param meters_per_second: The value in meters/second
    :type meters_per_second: float
    :return: The result in miles/hour
    :rtype: float
    """
    return meters_per_second / 0.44704


def mph_to_ms(miles_per_hour):
    """
    Convert miles/hour into meters/second

    :param miles_per_hour: The value in miles/hour
    :type miles_per_hour: float
    :return: The result in meters/second
    :rtype: float
    """
    return miles_per_hour * 0.44704


def ms_to_kn(meters_per_second):
    """
    Convert meters/second into knots (nautical miles/hour)

    :param meters_per_second: The value in meters/second
    :type meters_per_second: float
    :return: The result in knots (nautical miles/hour)
    :rtype: float
    """
    return meters_per_second * 3600 / 1852


def kn_to_ms(knots):
    """
    Convert knots (nautical miles/hour) into meters/second

    :param knots: The value in knots (nautical miles/hour)
    :type knots: float
    :return: The result in meters/second
    :rtype: float
    """
    return knots * 1852 / 3600
