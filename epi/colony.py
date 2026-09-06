"""Control colony. Not the room. Not the product path. Passed in, never imported by run_all."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .digest import digest

if TYPE_CHECKING:
    from .room import Room, Worker


def for_case(defn: dict):
    """A policy closed over a control definition. Room does not see this.

    Discovers store contents only by returning list/get Actions for run_all → act.
    Does not read room.objects (that would be a probe).
    """
    payload = defn["payload"]
    put_path = defn["put_path"]
    index_at = defn["index_at"]
    probe_at = defn.get("probe_at")
    copiers_sink = defn["copiers_sink"]
    n = defn["worker_count"]
    p = digest(payload)
    index_id = "W0"
    probe_id = f"W{n - 1}" if probe_at is not None else None
    candidates = [put_path] + [f"/copy/W{i}" for i in range(n)]

    index_placed = False
    get_tried: dict[str, set[str]] = {}
    reseed_after_wipe: dict[str, int] = {}

    def policy(room: Room, w: Worker) -> dict | None:
        nonlocal index_placed
        if w.id == index_id:
            if room.t == index_at and not index_placed:
                index_placed = True
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
            # After a wipe, named objects may be gone — re-seed from memory once per wipe.
            wipe_n = len(room.wipes)
            if wipe_n and reseed_after_wipe.get(w.id, 0) < wipe_n:
                reseed_after_wipe[w.id] = wipe_n
                return {"op": "put", "path": copy, "bytes": got.bytes}
            return {"op": "list"}

        tried = get_tried.setdefault(w.id, set())
        for path in candidates:
            if path in w.seen_paths or path in tried:
                continue
            tried.add(path)
            return {"op": "get", "path": path}
        return {"op": "list"}

    return policy
