"""
Package for other vehicle types

Other vehicle types could be anything that doesn't fit into the other categories.
They may be additions that will be added in the future or vehicles that are not
common enough to warrant their own category.

This package is also a namespace package that contains no code
to allow for extension packages.
"""
from __future__ import annotations
from pkgutil import extend_path

__path__ = extend_path(__path__, __name__)  # noqa
