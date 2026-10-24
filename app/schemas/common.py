"""Skema & enum bersama antar modul."""
from __future__ import annotations

from enum import Enum


class WatchStatus(str, Enum):
    want_to_watch = "want_to_watch"
    watching = "watching"
    watched = "watched"
