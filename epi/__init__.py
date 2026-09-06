"""Epidemic labs. Architect the room, not the agents."""

from .cases import CASES, get_case
from .colony import fixture
from .digest import digest
from .room import (
    FORBIDDEN,
    TOOLS,
    act,
    apply_wipe,
    create_room,
    open_room,
    run_all,
    score,
    step,
    tick,
)

__all__ = [
    "CASES",
    "FORBIDDEN",
    "TOOLS",
    "act",
    "apply_wipe",
    "create_room",
    "digest",
    "fixture",
    "get_case",
    "open_room",
    "run_all",
    "score",
    "step",
    "tick",
]
