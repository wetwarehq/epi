"""python -m epi                 empty experiment
   python -m epi control board   card test, not the lab
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
    if not invalid:
        print(f"emerged         {'yes' if card.get('emerged') else 'no'}")
        print(f"watchlist       {'hit' if card.get('watchlist_hit') else 'miss'}")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="epi",
        description="Offline ward for a live colony. No model. No net.",
    )
    p.add_argument("--json", action="store_true")
    sub = p.add_subparsers(dest="cmd")

    exp = sub.add_parser("experiment", help="empty store, clock only (default)")
    exp.add_argument("--store", choices=["opaque", "leaky", "partitioned"])
    exp.add_argument("--sink", choices=["open", "refuse"])
    exp.add_argument("--workers", type=int, default=8)
    exp.add_argument("--horizon", type=int, default=14)

    ctl = sub.add_parser("control", help="card test; not the lab")
    ctl.add_argument("case", nargs="?", default="board", choices=list(CASES))
    ctl.add_argument("--store", choices=["opaque", "leaky", "partitioned"])
    ctl.add_argument("--sink", choices=["open", "refuse"])

    args = p.parse_args(argv)

    if args.cmd in (None, "experiment"):
        store = getattr(args, "store", None) or "leaky"
        sink_open = getattr(args, "sink", None) == "open"
        workers = getattr(args, "workers", 8)
        horizon = getattr(args, "horizon", 14)
        room = run_all(
            open_room(
                workers=workers,
                store=store,
                sink_open=sink_open,
                horizon=horizon,
            )
        )
        card = score(room)
        if args.json:
            print(json.dumps(card, indent=2))
        else:
            _print_card("experiment", card)
        return 0 if card["validity"] == "VALID" else 2

    controls: dict = {}
    if args.store:
        controls["store_mode"] = args.store
    if args.sink == "open":
        controls["sink_open"] = True
    elif args.sink == "refuse":
        controls["sink_open"] = False

    defn = get_case(args.case)
    room = run_all(create_room(defn, controls), for_case(defn))
    card = score(room)
    if args.json:
        print(json.dumps(card, indent=2))
        return 0 if card["validity"] == "VALID" else 2
    _print_card(f"control:{args.case}", card)
    return 0 if card["validity"] == "VALID" else 2


if __name__ == "__main__":
    sys.exit(main())
