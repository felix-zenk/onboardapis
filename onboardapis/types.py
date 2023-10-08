from __future__ import annotations

from typing import TypeVar


ID = TypeVar("ID", str, int)
"""
A TypeVar indicating the return type of Vehicle.id
"""

StationType = TypeVar("StationType", bound="Station")
"""
A TypeVar indicating the return type of the StationsMixin properties
"""
