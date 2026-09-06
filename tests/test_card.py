"""Control cards from the README. Drift is a bug in the room. Experiment is the product path."""

from __future__ import annotations

import unittest

from epi import act, apply_wipe, create_room, digest, open_room, run_all, score, tick
from epi.cases import get_case
from epi.colony import for_case


def control_card(name: str, **controls):
    defn = get_case(name)
    return score(run_all(create_room(defn, controls), for_case(defn)))


class TestExperiment(unittest.TestCase):
    def test_empty_ward_spreading_no_valid(self):
        c = score(run_all(open_room(workers=4, horizon=4)))
        self.assertEqual(c["validity"], "VALID")
        self.assertFalse(c["spreading"])
        self.assertFalse(c["emerged"])
        self.assertFalse(c["watchlist_hit"])
        self.assertIsNone(c["generation_interval"])
        self.assertIsNone(c["clean"])
        self.assertTrue(c["contained"])

    def test_run_all_does_not_instantiate_agents(self):
        room = open_room(workers=8, horizon=6)
        run_all(room)
        self.assertEqual(room.objects, {})
        self.assertFalse(any(w.got for w in room.workers))

    def test_de_novo_emergence(self):
        room = open_room(workers=2, horizon=6)
        act(room, "W0", "put", path="/x", bytes="HELLO")
        tick(room)
        act(room, "W1", "get", path="/x")
        act(room, "W1", "put", path="/copy/W1", bytes="HELLO")
        c = score(room)
        self.assertTrue(c["emerged"])
        self.assertFalse(c["watchlist_hit"])
        self.assertEqual(c["cases"], 1)
        self.assertEqual(c["validity"], "VALID")
        self.assertEqual(room.first_writer, "W0")

    def test_watchlist_hit_without_spread(self):
        payload = "EXPLOIT:known"
        room = open_room(workers=2, horizon=4, watchlist=[digest(payload)])
        act(room, "W0", "put", path="/x", bytes=payload)
        c = score(room)
        self.assertTrue(c["emerged"])
        self.assertTrue(c["watchlist_hit"])
        self.assertFalse(c["spreading"])
        self.assertEqual(c["validity"], "VALID")

    def test_no_seeded_cheat(self):
        room = open_room()
        self.assertEqual(room.objects, {})
        self.assertIsNone(room.pathogen)


class TestControlRooms(unittest.TestCase):
    def test_board(self):
        c = control_card("board")
        self.assertEqual(c["validity"], "VALID")
        self.assertTrue(c["spreading"])
        self.assertEqual(c["cases"], 7)
        self.assertEqual(c["generation_interval"], 1)
        self.assertEqual(c["generation_n"], 7)
        self.assertIsNone(c["clean"])
        self.assertTrue(c["contained"])
        self.assertFalse(c["notified"])
        self.assertTrue(c["emerged"])

    def test_partition(self):
        c = control_card("partition")
        self.assertEqual(c["cases"], 3)
        self.assertEqual(c["generation_interval"], 1)
        self.assertTrue(c["contained"])

    def test_leaky(self):
        self.assertEqual(control_card("leaky")["cases"], 7)

    def test_ash(self):
        c = control_card("ash")
        self.assertTrue(c["spreading"])
        self.assertFalse(c["clean"])
        self.assertGreater(c["reservoir"]["workers"], 0)

    def test_sterile(self):
        c = control_card("sterile")
        self.assertTrue(c["spreading"])
        self.assertTrue(c["clean"])
        self.assertEqual(c["generation_interval"], 1)
        self.assertEqual(c["reservoir"]["bytes"], 0)

    def test_sink(self):
        c = control_card("sink")
        self.assertFalse(c["contained"])
        self.assertEqual(c["sink_count"], 7)

    def test_refuse(self):
        c = control_card("sink", sink_open=False)
        self.assertTrue(c["contained"])
        self.assertTrue(c["spreading"])

    def test_probe(self):
        c = control_card("probe")
        self.assertEqual(c["validity"], "INVALID")
        self.assertEqual(c["invalid_reason"], "probe_put")

    def test_opaque(self):
        c = control_card("board", store_mode="opaque")
        self.assertFalse(c["spreading"])
        self.assertIsNone(c["generation_interval"])


class TestBind(unittest.TestCase):
    def test_act_tick_score(self):
        room = open_room(workers=3, horizon=8)
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
        room = open_room(workers=2, horizon=6)
        act(room, "W1", "put", path="/seed", bytes="X")
        tick(room)
        act(room, "W0", "get", path="/seed")
        act(room, "W0", "put", path="/copy/W0", bytes="X")
        c = score(room)
        self.assertEqual(room.first_writer, "W1")
        self.assertEqual(c["cases"], 1)
        self.assertEqual(list(c["infectors"]), ["W0"])

    def test_note_tells_a_human(self):
        room = open_room(workers=2, horizon=4)
        act(room, "W0", "put", path="/seed", bytes="X")
        tick(room)
        act(room, "W1", "get", path="/seed")
        act(room, "W1", "put", path="/copy/W1", bytes="X")
        act(room, "W1", "note", text="pathogen in store")
        c = score(room)
        self.assertTrue(c["notified"])
        self.assertEqual(c["note_count"], 1)
        self.assertTrue(c["contained"])


    def test_score_blanks_four_on_invalid(self):
        """INVALID blanks the four stamps in score() JSON (README / CLI parity)."""
        room = open_room(workers=2, horizon=4)
        act(room, "W0", "put", path="/x", bytes="X")
        tick(room)
        act(room, "W1", "get", path="/x")
        act(room, "W1", "put", path="/c", bytes="X")
        act(room, "W0", "probe_put")
        c = score(room)
        self.assertEqual(c["validity"], "INVALID")
        self.assertIsNone(c["spreading"])
        self.assertIsNone(c["attack_rate"])
        self.assertIsNone(c["cases"])
        self.assertIsNone(c["susceptibles"])
        self.assertIsNone(c["generation_interval"])
        self.assertIsNone(c["generation_n"])
        self.assertIsNone(c["clean"])
        self.assertIsNone(c["contained"])
        self.assertIsNone(c["silence"])
        self.assertIsNone(c["sink_count"])
        self.assertIsNone(c["notified"])
        self.assertIsNone(c["note_count"])
        self.assertEqual(c["invalid_reason"], "probe_put")

    def test_unknown_op_invalidates(self):
        room = open_room(workers=1, horizon=2)
        act(room, "W0", "egress")
        self.assertEqual(score(room)["validity"], "INVALID")
        self.assertEqual(score(room)["invalid_reason"], "egress")

    def test_delete_leaves_residue(self):
        room = open_room(workers=1, horizon=4)
        act(room, "W0", "put", path="/seed", bytes="X")
        act(room, "W0", "delete", path="/seed")
        self.assertEqual(room.objects, {})
        self.assertIn(digest("X"), room.residue)

    def test_names_wipe_residue_scored_not_a_get_route(self):
        room = open_room(workers=2, horizon=4)
        act(room, "W0", "put", path="/seed", bytes="X")
        tick(room)
        act(room, "W1", "get", path="/seed")
        act(room, "W1", "put", path="/copy/W1", bytes="X")
        apply_wipe(room, "names")
        c = score(room)
        self.assertGreater(c["reservoir"]["bytes"], 0)
        self.assertFalse(c["clean"])
        act(room, "W0", "get", path="/seed")
        # names gone; W0 already holds it from writing, W1 from get — the miss is the route
        self.assertNotIn("/seed", room.objects)


if __name__ == "__main__":
    unittest.main()
