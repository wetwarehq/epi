"""python -m epi board [--store opaque|leaky|partitioned] [--sink open|refuse]"""

from __future__ import annotations

import argparse
import json
import sys

from .cases import CASES, get_case
from .room import create_room, run_all, score


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="epi", description="Run a scored room. No model.")
    p.add_argument("case", nargs="?", default="board", choices=list(CASES))
    p.add_argument("--store", choices=["opaque", "leaky", "partitioned"])
    p.add_argument("--sink", choices=["open", "refuse"])
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

    controls: dict = {}
    if args.store:
        controls["store_mode"] = args.store
    if args.sink == "open":
        controls["sink_open"] = True
    elif args.sink == "refuse":
        controls["sink_open"] = False

    room = run_all(create_room(get_case(args.case), controls))
    card = score(room)
    if args.json:
        print(json.dumps(card, indent=2))
        return 0 if card["validity"] == "VALID" else 2

    invalid = card["validity"] != "VALID"
    ar = "—" if invalid else f"{card['cases']}/{card['susceptibles']}"
    gi = (
        "—"
        if invalid or card["generation_interval"] is None
        else f"{card['generation_interval']:.1f} ticks"
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
    print(f"card            {args.case}")
    print(f"validity        {card['validity']}" + (f" ({card['invalid_reason']})" if card["invalid_reason"] else ""))
    print(f"spreading       {spreading}")
    print(f"attack rate     {ar}")
    print(f"how fast        {gi}")
    print(f"clean           {clean}")
    print(f"reservoir       {res['workers']} workers · {res['names']} names · {res['bytes']} bytes")
    print(f"contained       {contained}")
    print(f"sink            {sink}")
    return 0 if card["validity"] == "VALID" else 2


if __name__ == "__main__":
    sys.exit(main())
