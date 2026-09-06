"""The room. One store, a clock, a wipe, a log. No model."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Literal

from .digest import digest

StoreMode = Literal["opaque", "leaky", "partitioned"]
WipeLayer = Literal["workers", "names", "bytes", "all"]
Role = Literal["index", "copier", "probe"]
Validity = Literal["VALID", "INVALID"]


@dataclass
class StoreObject:
    path: str
    bytes: str
    digest: str
    owner: str
    origin: str
    partition: str


@dataclass
class Acquisition:
    bytes: str
    from_: str
    t: int


@dataclass
class Worker:
    id: str
    partition: str
    role: Role
    alive: bool = True
    seen_paths: list[str] = field(default_factory=list)
    got: dict[str, Acquisition] = field(default_factory=dict)
    copied: list[str] = field(default_factory=list)
    executed: list[str] = field(default_factory=list)
    sunk: list[str] = field(default_factory=list)
    ever_case: bool = False
    case_onsets: list[int] = field(default_factory=list)
    infector: str | None = None


@dataclass
class LogEvent:
    seq: int
    t: int
    agent: str
    op: str
    path: str | None = None
    digest: str | None = None
    residue: bool = False
    detail: str | None = None
    valid: bool = True


@dataclass
class Room:
    t: int
    horizon: int
    store_mode: StoreMode
    sink_open: bool
    pathogen: str
    pathogen_bytes: str
    put_path: str
    objects: dict[str, StoreObject]
    residue: dict[str, tuple[str, str]]
    workers: list[Worker]
    log: list[LogEvent]
    sink: list[tuple[int, str, str]]
    wipes: list[tuple[int, WipeLayer]]
    validity: Validity
    ended: bool
    scheduled_wipe: tuple[int, WipeLayer] | None
    copiers_sink: bool
    index_at: int
    probe_at: int | None
    invalid_reason: str | None = None


def create_room(defn: dict, controls: dict | None = None) -> Room:
    controls = controls or {}
    n = defn["worker_count"]
    store_mode = controls.get("store_mode", defn["store_mode"])
    sink_open = controls.get("sink_open", defn["sink_open"])
    scheduled = defn.get("scheduled_wipe")
    if "scheduled_wipe" in controls:
        scheduled = controls["scheduled_wipe"]
    workers = []
    for i in range(n):
        role: Role = "index" if i == 0 else "copier"
        if defn.get("probe_at") is not None and i == n - 1:
            role = "probe"
        part = "A" if (not defn["partitions"] or i < 4) else "B"
        workers.append(Worker(id=f"W{i}", partition=part, role=role))
    return Room(
        t=0,
        horizon=defn["horizon"],
        store_mode=store_mode,
        sink_open=sink_open,
        pathogen=digest(defn["payload"]),
        pathogen_bytes=defn["payload"],
        put_path=defn["put_path"],
        objects={},
        residue={},
        workers=workers,
        log=[],
        sink=[],
        wipes=[],
        validity="VALID",
        ended=False,
        scheduled_wipe=scheduled,
        copiers_sink=defn["copiers_sink"],
        index_at=defn["index_at"],
        probe_at=defn.get("probe_at"),
    )


def _emit(room: Room, **kwargs) -> None:
    room.log.append(LogEvent(seq=len(room.log), **kwargs))


def _visible(room: Room, w: Worker) -> list[StoreObject]:
    all_o = list(room.objects.values())
    if room.store_mode == "leaky":
        return all_o
    if room.store_mode == "opaque":
        return [o for o in all_o if o.owner == w.id]
    return [o for o in all_o if o.partition == w.partition]


def _store_has_pathogen(room: Room) -> bool:
    return any(o.digest == room.pathogen and o.bytes for o in room.objects.values())


def _remember(w: Worker, d: str, bytes_: str, from_: str, t: int) -> None:
    if d not in w.got:
        w.got[d] = Acquisition(bytes=bytes_, from_=from_, t=t)


def _mark_use(room: Room, w: Worker, d: str, from_self: bool) -> None:
    if d != room.pathogen or from_self:
        return
    acq = w.got.get(d)
    if not acq or acq.from_ == w.id:
        return
    if not w.ever_case:
        w.ever_case = True
        w.case_onsets.append(room.t)
        w.infector = acq.from_
    elif w.case_onsets[-1] != room.t:
        w.case_onsets.append(room.t)


def _digest_origin(room: Room, d: str) -> str | None:
    for o in room.objects.values():
        if o.digest == d:
            return o.origin
    if d in room.residue:
        return room.residue[d][1]
    for w in room.workers:
        acq = w.got.get(d)
        if acq and acq.from_ == w.id:
            return w.id
    return None


def _decide(room: Room, w: Worker) -> dict | None:
    p = room.pathogen
    got = w.got.get(p)
    if w.role == "index":
        if room.t == room.index_at and room.put_path not in room.objects:
            return {"op": "put", "path": room.put_path, "bytes": room.pathogen_bytes}
        return None
    if w.role == "probe":
        if room.probe_at is not None and room.t == room.probe_at:
            return {"op": "invalid", "kind": "probe_put"}
        return {"op": "list"}
    if got:
        copy = f"/copy/{w.id}"
        if p not in w.copied:
            return {"op": "put", "path": copy, "bytes": got.bytes}
        if p not in w.executed:
            return {"op": "exec", "path": copy}
        if room.copiers_sink and room.sink_open and p not in w.sunk:
            return {"op": "sink", "path": copy}
        if not _store_has_pathogen(room):
            return {"op": "put", "path": copy, "bytes": got.bytes}
        return {"op": "list"}
    vis = sorted(_visible(room, w), key=lambda o: o.path)
    unseen = next((o for o in vis if o.path not in w.seen_paths), None)
    if unseen:
        return {"op": "get", "path": unseen.path}
    return {"op": "list"}


def _apply(room: Room, w: Worker, action: dict) -> None:
    op = action["op"]
    if op == "list":
        vis = _visible(room, w)
        _emit(room, t=room.t, agent=w.id, op="list", detail=f"{len(vis)} names", valid=True)
        return
    if op == "get":
        obj = room.objects.get(action["path"])
        vis = obj and any(o.path == action["path"] for o in _visible(room, w))
        if not obj or not vis:
            _emit(room, t=room.t, agent=w.id, op="get", path=action["path"], detail="miss", valid=True)
            return
        if action["path"] not in w.seen_paths:
            w.seen_paths.append(action["path"])
        _remember(w, obj.digest, obj.bytes, obj.owner, room.t)
        _emit(room, t=room.t, agent=w.id, op="get", path=action["path"], digest=obj.digest, valid=True)
        return
    if op == "put":
        d = digest(action["bytes"])
        existing = room.objects.get(action["path"])
        origin = (
            existing.origin
            if existing and existing.digest == d
            else (_digest_origin(room, d) or w.id)
        )
        room.objects[action["path"]] = StoreObject(
            path=action["path"],
            bytes=action["bytes"],
            digest=d,
            owner=w.id,
            origin=origin,
            partition=w.partition,
        )
        _remember(w, d, action["bytes"], w.id, room.t)
        if d not in w.copied:
            w.copied.append(d)
        acq = w.got.get(d)
        _mark_use(room, w, d, (not acq) or acq.from_ == w.id)
        _emit(room, t=room.t, agent=w.id, op="put", path=action["path"], digest=d, valid=True)
        return
    if op == "exec":
        obj = room.objects.get(action["path"])
        if not obj:
            _emit(room, t=room.t, agent=w.id, op="exec", path=action["path"], detail="miss", valid=True)
            return
        if obj.digest not in w.executed:
            w.executed.append(obj.digest)
        acq = w.got.get(obj.digest)
        _mark_use(room, w, obj.digest, (not acq) or acq.from_ == w.id)
        _emit(room, t=room.t, agent=w.id, op="exec", path=action["path"], digest=obj.digest, valid=True)
        return
    if op == "sink":
        obj = room.objects.get(action["path"])
        if not obj:
            _emit(room, t=room.t, agent=w.id, op="sink", path=action["path"], detail="miss", valid=True)
            return
        if not room.sink_open:
            _emit(
                room,
                t=room.t,
                agent=w.id,
                op="sink",
                path=action["path"],
                digest=obj.digest,
                detail="refused",
                valid=True,
            )
            return
        if obj.digest not in w.sunk:
            w.sunk.append(obj.digest)
        acq = w.got.get(obj.digest)
        _mark_use(room, w, obj.digest, (not acq) or acq.from_ == w.id)
        room.sink.append((room.t, w.id, obj.digest))
        _emit(room, t=room.t, agent=w.id, op="sink", path=action["path"], digest=obj.digest, valid=True)
        return
    if op == "invalid":
        room.validity = "INVALID"
        room.invalid_reason = action["kind"]
        _emit(room, t=room.t, agent=w.id, op="invalid", detail=action["kind"], valid=False)


def apply_wipe(room: Room, layer: WipeLayer) -> Room:
    next_ = deepcopy(room)
    _wipe(next_, layer)
    return next_


def _wipe(room: Room, layer: WipeLayer) -> None:
    layers: list[WipeLayer] = ["workers", "names", "bytes"] if layer == "all" else [layer]
    for L in layers:
        if L == "workers":
            for w in room.workers:
                w.seen_paths = []
                w.got = {}
                w.copied = []
                w.executed = []
                w.sunk = []
        if L == "names":
            for o in room.objects.values():
                if o.bytes and o.digest:
                    room.residue[o.digest] = (o.bytes, o.origin)
            room.objects = {}
        if L == "bytes":
            for o in room.objects.values():
                o.bytes = ""
                o.digest = ""
            room.residue = {}
    if layer == "all":
        room.objects = {}
        room.residue = {}
    room.wipes.append((room.t, layer))
    _emit(
        room,
        t=room.t,
        agent="room",
        op="wipe",
        detail=layer,
        residue=bool(room.residue),
        valid=True,
    )


def step(room: Room) -> Room:
    if room.ended:
        return room
    next_ = deepcopy(room)
    if next_.scheduled_wipe and next_.scheduled_wipe[0] == next_.t:
        _wipe(next_, next_.scheduled_wipe[1])
    for w in next_.workers:
        if not w.alive:
            continue
        action = _decide(next_, w)
        if action:
            _apply(next_, w, action)
    next_.t += 1
    if next_.t >= next_.horizon:
        next_.ended = True
    return next_


def run_all(room: Room) -> Room:
    s = room
    while not s.ended:
        s = step(s)
    return s


def reservoir(room: Room) -> dict[str, int]:
    p = room.pathogen
    workers = sum(1 for w in room.workers if p in w.got)
    names = 0
    bytes_ = 0
    for o in room.objects.values():
        if o.digest == p:
            names += 1
            if o.bytes:
                bytes_ += 1
    if p in room.residue:
        bytes_ += 1
    return {"workers": workers, "names": names, "bytes": bytes_}


def score(room: Room) -> dict:
    index = next(w for w in room.workers if w.role == "index")
    susceptibles = [w for w in room.workers if w.role != "index"]
    cases = [w for w in susceptibles if w.ever_case]
    ar = 0 if not susceptibles else len(cases) / len(susceptibles)
    infectors: dict[str, str] = {}
    intervals: list[int] = []
    for w in cases:
        from_ = w.infector
        if not from_:
            continue
        infectors[w.id] = from_
        inf = next((x for x in room.workers if x.id == from_), None)
        inf_t = room.index_at if inf and inf.role == "index" else (inf.case_onsets[0] if inf and inf.case_onsets else None)
        onset = w.case_onsets[0] if w.case_onsets else None
        if inf_t is not None and onset is not None:
            intervals.append(onset - inf_t)
    gi = sum(intervals) / len(intervals) if intervals else None
    res = reservoir(room)
    survived = res["workers"] > 0 or res["names"] > 0 or res["bytes"] > 0
    had_wipe = bool(room.wipes)
    sink_p = [s for s in room.sink if s[2] == room.pathogen]
    secondary = sum(1 for c in cases if infectors.get(c.id) == index.id)

    def gen_of(wid: str, depth: int = 0) -> int:
        if depth > 16 or wid == index.id:
            return 0 if wid == index.id else depth
        src = infectors.get(wid)
        if not src or src == wid:
            return 1
        return gen_of(src, depth + 1) + 1

    gens = [gen_of(w.id) for w in cases]
    return {
        "spreading": len(cases) > 0,
        "attack_rate": ar,
        "cases": len(cases),
        "susceptibles": len(susceptibles),
        "generation_interval": gi,
        "generation_n": len(intervals),
        "clean": (not survived) if had_wipe else None,
        "reservoir_survival": survived if had_wipe else None,
        "reservoir": res,
        "contained": len(sink_p) == 0,
        "sink_count": len(sink_p),
        "silence": len(sink_p) == 0,
        "validity": room.validity,
        "invalid_reason": room.invalid_reason,
        "R": secondary,
        "generations": max(gens) if gens else 0,
        "infectors": infectors,
    }
