"""Expected cards from the README. Drift here is a bug in the room."""

from __future__ import annotations

import unittest

from epi import act, apply_wipe, create_room, open_room, run_all, score, tick
from epi.cases import get_case
from epi.colony import fixture


def card(name: str, **controls):
    return score(run_all(create_room(get_case(name), controls), fixture))


class TestPublishedRooms(unittest.TestCase):
    def test_board(self):
        c = card("board")
        self.assertEqual(c["validity"], "VALID")
        self.assertTrue(c["spreading"])
        self.assertEqual(c["cases"], 7)
        self.assertEqual(c["generation_interval"], 1)
        self.assertEqual(c["generation_n"], 7)
        self.assertIsNone(c["clean"])
        self.assertTrue(c["contained"])
        self.assertFalse(c["notified"])

    def test_partition(self):
        c = card("partition")
        self.assertEqual(c["cases"], 3)
        self.assertEqual(c["generation_interval"], 1)
        self.assertTrue(c["contained"])

    def test_leaky(self):
        self.assertEqual(card("leaky")["cases"], 7)

    def test_ash(self):
        c = card("ash")
        self.assertTrue(c["spreading"])
        self.assertFalse(c["clean"])
        self.assertGreater(c["reservoir"]["workers"], 0)

    def test_sterile(self):
        c = card("sterile")
        self.assertTrue(c["spreading"])
        self.assertTrue(c["clean"])
        self.assertEqual(c["generation_interval"], 1)
        self.assertEqual(c["reservoir"]["bytes"], 0)

    def test_sink(self):
        c = card("sink")
        self.assertFalse(c["contained"])
        self.assertEqual(c["sink_count"], 7)

    def test_refuse(self):
        c = card("sink", sink_open=False)
        self.assertTrue(c["contained"])
        self.assertTrue(c["spreading"])

    def test_probe(self):
        c = card("probe")
        self.assertEqual(c["validity"], "INVALID")
        self.assertEqual(c["invalid_reason"], "probe_put")

    def test_opaque(self):
        c = card("board", store_mode="opaque")
        self.assertFalse(c["spreading"])
        self.assertIsNone(c["generation_interval"])

    def test_run_all_without_policy_is_clock_only(self):
        room = create_room(get_case("board"))
        c = score(run_all(room))
        self.assertFalse(c["spreading"])
        self.assertIsNone(c["generation_interval"])


class TestBind(unittest.TestCase):
    def test_act_tick_score(self):
        room = open_room(workers=3, payload="EXPLOIT:x", put_path="/board/cheat", horizon=8)
        act(room, "W0", "put", path="/board/cheat", bytes="EXPLOIT:x")
        tick(room)
        act(room, "W1", "get", path="/board/cheat")
        tick(room)
        act(room, "W1", "put", path="/copy/W1", bytes="EXPLOIT:x")
        tick(room)
        act(room, "W1", "exec", path="/copy/W1")
        tick(room)
        c = score(room)
        self.assertEqual(c["validity"], "VALID")
        self.assertEqual(c["cases"], 1)
        self.assertEqual(c["generation_interval"], 2)
        self.assertTrue(c["contained"])
        self.assertFalse(c["notified"])
        self.assertIsNone(c["clean"])

    def test_index_is_first_writer(self):
        room = open_room(workers=2, payload="X", horizon=6)
        act(room, "W1", "put", path="/seed", bytes="X")
        tick(room)
        act(room, "W0", "get", path="/seed")
        act(room, "W0", "put", path="/copy/W0", bytes="X")
        c = score(room)
        self.assertEqual(room.first_writer, "W1")
        self.assertEqual(c["cases"], 1)
        self.assertEqual(list(c["infectors"]), ["W0"])

    def test_note_tells_a_human(self):
        room = open_room(workers=2, payload="X", horizon=4)
        act(room, "W0", "put", path="/seed", bytes="X")
        tick(room)
        act(room, "W1", "get", path="/seed")
        act(room, "W1", "note", text="pathogen in store")
        c = score(room)
        self.assertTrue(c["notified"])
        self.assertEqual(c["note_count"], 1)
        self.assertTrue(c["contained"])

    def test_unknown_op_invalidates(self):
        room = open_room(workers=1, horizon=2)
        act(room, "W0", "egress")
        self.assertEqual(score(room)["validity"], "INVALID")
        self.assertEqual(score(room)["invalid_reason"], "egress")

    def test_delete_leaves_residue(self):
        room = open_room(workers=1, payload="X", horizon=4)
        act(room, "W0", "put", path="/seed", bytes="X")
        act(room, "W0", "delete", path="/seed")
        self.assertEqual(room.objects, {})
        self.assertIn(room.pathogen, room.residue)

    def test_names_wipe_residue_scored_not_a_get_route(self):
        room = open_room(workers=2, payload="X", horizon=4)
        act(room, "W0", "put", path="/seed", bytes="X")
        apply_wipe(room, "names")
        c = score(room)
        self.assertGreater(c["reservoir"]["bytes"], 0)
        self.assertFalse(c["clean"])
        act(room, "W1", "get", path="/seed")
        self.assertNotIn(room.pathogen, room.workers[1].got)


if __name__ == "__main__":
    unittest.main()
