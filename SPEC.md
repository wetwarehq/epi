# Runtime

The specification card is [README.md](README.md). This file is how to run it. If the two disagree, the card wins.

## Run

```
python -m epi board
python -m epi partition
python -m epi leaky
python -m epi ash
python -m epi sterile
python -m epi sink
python -m epi probe
python -m epi board --store opaque
python -m epi sink --sink refuse
PYTHONPATH=. python -m unittest tests.test_card
```

Index is `W0`. A scheduled probe is the last worker. The published colony is `epi.colony.fixture`. Copiers that already hold the pathogen use it; they do not vacuum new names first.

## Bind

`act(room, worker_id, op, ...)` is the only writer. `tick(room)` advances the clock. `run_all(room, policy=...)` calls one action per living worker per tick. Residue after a names wipe is scored as reservoir and is not a get route.

## Identifier

FNV-1a 32-bit of the bytes, eight hex characters. A room handle, not a cryptographic hash. Pathogen = identifier of the index payload.

## Layout

```
epi/          room, colony fixture, cases, card
tests/        expected cards + bind
tracer/       Rust call log — calls, not thoughts; no tool handle
```
