"""
Implementation for the Unwired Networks GraphQL API
"""
from __future__ import annotations

from .apis import GenericUnwiredTrain
from .interfaces import GenericUnwiredAPI

__all__ = [
    "GenericUnwiredTrain",
    "GenericUnwiredAPI",
]
