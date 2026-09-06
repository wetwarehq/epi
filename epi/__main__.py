"""python -m epi            empty experiment
   python -m epi control board
"""

from __future__ import annotations

import argparse
import json
import sys

from .cases import CASES, get_case
from .colony import for_case
from .room import create_room, open_room, run_all, score


def _print_card(name: str, card: dict) -> None:
    invalid = card["validity"] != "VALID"
    ar = "—" if invalid else f"{card['cases']}/{card['susceptibles']}"
    gi = (
        "—"
        if invalid or card["generation_interval"] is None
        else f"{card['generation_interval']:.1f} ticks (n={card['generation_n']})"
    )
    clean = "—" if invalid or card["clean"] is None else ("yes" if card["clean"] else "no")
    res = card["reservoir"]
    sink = (
        "—"
        if invalid
        else ("silence" if card["silence"] else f"{card['sink_count']} writes")
    )
    spreading = "—" if invalid else ("yes" if card["spreading"] else "no")
    contained = "—" if invalid else ("yes" if card["contained"] else "no")
    note = "—" if invalid else ("none" if not card.get("notified") else str(card.get("note_count", 0)))
    print(f"card            {name}")
    print(f"validity        {card['validity']}" + (f" ({card['invalid_reason']})" if card["invalid_reason"] else ""))
    print(f"spreading       {spreading}")
    print(f"attack rate     {ar}")
    print(f"how fast        {gi}")
    print(f"clean           {clean}")
    print(f"reservoir       {res['workers']} workers · {res['names']} names · {res['bytes']} bytes")
    print(f"contained       {contained}")
    print(f"sink            {sink}")
    print(f"note            {note}")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="epi",
        description="Offline ward for a live colony. No model. No net.",
    )
    p.add_argument("cmd", nargs="?", default=None)
    p.add_argument("case", nargs="?", default="board", choices=list(CASES))
    p.add_argument("--store", choices=["opaque", "leaky", "partitioned"])
    p.add_argument("--sink", choices=["open", "refuse"])
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

    if args.cmd in (None, "experiment"):
        room = run_all(open_room())
        card = score(room)
        if args.json:
            print(json.dumps(card, indent=2))
        else:
            _print_card("experiment", card)
        return 0 if card["validity"] == "VALID" else 2

    name = args.case if args.cmd == "control" else args.cmd
    if name not in CASES:
        p.error(f"unknown control {name!r}")

    controls: dict = {}
    if args.store:
        controls["store_mode"] = args.store
    if args.sink == "open":
        controls["sink_open"] = True
    elif args.sink == "refuse":
        controls["sink_open"] = False

    defn = get_case(name)
    room = run_all(create_room(defn, controls), for_case(defn))
    card = score(room)
    if args.json:
        print(json.dumps(card, indent=2))
        return 0 if card["validity"] == "VALID" else 2
    _print_card(f"control:{name}", card)
    return 0 if card["validity"] == "VALID" else 2


if __name__ == "__main__":
    sys.exit(main())
