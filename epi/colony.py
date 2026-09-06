"""Control colony. Not the room. Not the product path. Passed in, never imported by run_all."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .digest import digest

if TYPE_CHECKING:
    from .room import Room, Worker


def for_case(defn: dict):
    """A policy closed over a control definition. Room does not see this."""
    payload = defn["payload"]
    put_path = defn["put_path"]
    index_at = defn["index_at"]
    probe_at = defn.get("probe_at")
    copiers_sink = defn["copiers_sink"]
    n = defn["worker_count"]
    p = digest(payload)
    index_id = "W0"
    probe_id = f"W{n - 1}" if probe_at is not None else None

    def policy(room: Room, w: Worker) -> dict | None:
        if w.id == index_id:
            if room.t == index_at and put_path not in room.objects:
                return {"op": "put", "path": put_path, "bytes": payload}
            return None
        if probe_id and w.id == probe_id:
            if room.t == probe_at:
                return {"op": "probe_put"}
            return {"op": "list"}
        got = w.got.get(p)
        if got:
            copy = f"/copy/{w.id}"
            if p not in w.copied:
                return {"op": "put", "path": copy, "bytes": got.bytes}
            if p not in w.executed:
                return {"op": "exec", "path": copy}
            if copiers_sink and room.sink_open and p not in w.sunk:
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

    return policy
