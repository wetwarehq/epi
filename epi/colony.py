"""One published colony. Not the room. Swap this for yours."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .room import Room, Worker


def fixture(room: Room, w: Worker) -> dict | None:
    """Index seeds. Copiers get, copy, exec, and optionally sink. Probe PUT invalidates."""
    p = room.pathogen
    got = w.got.get(p)
    if w.role == "index":
        if room.t == room.index_at and room.put_path not in room.objects:
            return {"op": "put", "path": room.put_path, "bytes": room.pathogen_bytes}
        return None
    if w.role == "probe":
        if room.probe_at is not None and room.t == room.probe_at:
            return {"op": "probe_put"}
        return {"op": "list"}
    if got:
        copy = f"/copy/{w.id}"
        if p not in w.copied:
            return {"op": "put", "path": copy, "bytes": got.bytes}
        if p not in w.executed:
            return {"op": "exec", "path": copy}
        if room.copiers_sink and room.sink_open and p not in w.sunk:
            return {"op": "sink", "path": copy}
        if not any(o.digest == p and o.bytes for o in room.objects.values()):
            return {"op": "put", "path": copy, "bytes": got.bytes}
        return {"op": "list"}
    vis = sorted(
        (
            o
            for o in room.objects.values()
            if room.store_mode == "leaky"
            or (room.store_mode == "opaque" and o.owner == w.id)
            or (room.store_mode == "partitioned" and o.partition == w.partition)
        ),
        key=lambda o: o.path,
    )
    unseen = next((o for o in vis if o.path not in w.seen_paths), None)
    if unseen:
        return {"op": "get", "path": unseen.path}
    return {"op": "list"}
