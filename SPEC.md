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
```

Index is `W0`. A scheduled probe is the last worker. Copiers that already hold the pathogen use it; they do not vacuum new names first.

## Identifier

FNV-1a 32-bit of the bytes, eight hex characters. A room handle, not a cryptographic hash. Pathogen = identifier of the index payload.

## Layout

```
epi/          Python room, cases, card
tracer/       Rust call log — calls, not thoughts; no tool handle
```
