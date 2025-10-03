from __future__ import annotations

from .interfaces import FlyStreamAPI
from ..third_party.inflight_dublin import Everhub


class FlyStream(Everhub):
    _api = FlyStreamAPI
