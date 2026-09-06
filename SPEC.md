# Runtime

[README.md](README.md) is the specification (the law). This file is how to run it. Where code disagrees, **README wins**.

## Experiment (the lab)

```
python -m epi
```

Empty store, clock only, card `spreading no` VALID. Bind a colony with `open_room` / `act` / `tick` / `score`. `run_all(room)` does not import a colony.

```
from epi import TOOLS, FORBIDDEN, open_room, act, tick, apply_wipe, score, create_room, run_all, digest
```

## Control (tests of the card)

```
python -m epi control board
PYTHONPATH=. python -m unittest tests.test_card
```

`epi.colony.for_case` is input. The room has no roles. `python -m epi board` is not a command.

## Identifier

FNV-1a 32-bit of the bytes, eight hex characters. Pathogen emerges: watchlist put, or first digest a second worker uses.

## Layout

```
epi/          room (no colony), control cases, control policy
tests/        experiment + control cards
tracer/       typed Call log — not wired; no tool handle
```

## Offline

Offline is how you deploy the process. It is not a fifth stamp. The room does not open sockets; it also cannot deny a socket the host already has.
