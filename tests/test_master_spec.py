#!/usr/bin/env python3
"""
Comprehensive Unit Tests for ANTIGRAVITY_MASTER_SPEC.md implementation in fcr_repl.py and fcr_analyzer.py.
"""

import os
import shutil
import unittest
import math
import cmath
from fcr_repl import FCRStateGraph, REPOS_DIR
from fcr_analyzer import analyze

class TestFCRMasterSpec(unittest.TestCase):

    def setUp(self):
        if os.path.exists(REPOS_DIR):
            shutil.rmtree(REPOS_DIR)

    def tearDown(self):
        if os.path.exists(REPOS_DIR):
            shutil.rmtree(REPOS_DIR)

    def test_attractor_wedge_product_init(self):
        # Default initialization should produce M6_M3^4 octahedral frame with active edges
        g = FCRStateGraph()
        self.assertEqual(g.n, 6)
        # Verify active correlations (not disconnected infs)
        self.assertGreater(abs(g.correlation_matrix[0][1]), 0.0)
        self.assertGreater(abs(g.correlation_matrix[0][2]), 0.0)

        # M3^2 wedge product (5 nodes)
        g_wedge = FCRStateGraph("M3^2")
        self.assertEqual(g_wedge.n, 5)
        self.assertGreater(abs(g_wedge.correlation_matrix[0][1]), 0.0)
        self.assertGreater(abs(g_wedge.correlation_matrix[0][3]), 0.0)

    def test_geodesic_distance(self):
        g = FCRStateGraph("M3_triangle")
        # Direct distance
        self.assertEqual(g.get_geodesic_distance(0, 1), 1.0)

    def test_capacity_coherent_scaling_and_venting(self):
        g = FCRStateGraph("M3_triangle")
        # Overload node 0 capacity past 1.0: 0.8^2 + 0.8^2 = 1.28 > 1.0
        g.set_edge(0, 1, 1.0, 0.8 + 0.0j)
        g.set_edge(0, 2, 1.0, 0.8 + 0.0j)

        res = g.virtual_lock_normalize()
        self.assertEqual(len(res["vent_events"]), 1)
        self.assertAlmostEqual(res["vent_events"][0]["delta_S"], 0.28, places=4)
        # Norm after coherent scaling must be exactly 1.0
        self.assertAlmostEqual(g.capacity_sum(0), 1.0, places=5)

    def test_link_severing_and_fission(self):
        g = FCRStateGraph("M3_triangle")
        # Sever link between 1 and 2 by setting correlation to noise < 10^-6
        g.set_edge(1, 2, 1.0, 1.0e-7)

        res = g.virtual_lock_normalize()
        self.assertEqual(res["severed_count"], 1)

    def test_boundary_seed_templates(self):
        # 1. M3_triangle
        g3 = FCRStateGraph("M3_triangle")
        self.assertEqual(g3.n, 3)
        self.assertEqual(g3.correlation_matrix[0][1], 0.5 + 0j)

        # 2. M6_octahedron
        g6 = FCRStateGraph("M6_octahedron")
        self.assertEqual(g6.n, 6)

        # 3. M6_M3^4
        g_wedge = FCRStateGraph("M6_M3^4")
        self.assertEqual(g_wedge.n, 6)

    def test_canonical_hash_uniqueness(self):
        g1 = FCRStateGraph("M3_triangle")
        g2 = FCRStateGraph("M3_triangle")

        h1 = g1.compute_canonical_hash()
        h2 = g2.compute_canonical_hash()
        self.assertEqual(h1, h2)
        self.assertEqual(len(h1), 8)

    def test_triangulation_warnings(self):
        g = FCRStateGraph()
        g._init_blank(4)
        g.set_edge(0, 1, 1.0, 0.5)
        g.set_edge(1, 2, 1.0, 0.5)

        # 1. Triangulation on open path 0 -> 1 -> 2 adds new edge (0, 2)
        prod = g.triangulate(0, 1, 2)
        self.assertEqual(prod, 0.25)
        self.assertEqual(g.correlation_matrix[0][2], 0.25)

        # 2. Triangulation when edge (0, 2) already exists -> raises ValueError
        with self.assertRaises(ValueError) as cm1:
            g.triangulate(0, 1, 2)
        self.assertIn("already exists", str(cm1.exception))

        # 3. Triangulation when target edge (0, 3) does not exist, but edge (1, 3) is 0 -> raises ValueError
        with self.assertRaises(ValueError) as cm2:
            g.triangulate(0, 1, 3)
        self.assertIn("is 0", str(cm2.exception))

    def test_repository_export_and_analyzer(self):
        g = FCRStateGraph()
        g._init_blank(4)
        g.set_edge(0, 1, 1.0, 0.5)
        g.set_edge(1, 2, 1.0, 0.5)
        g.triangulate(0, 1, 2)
        file_path = g.step_and_save()

        self.assertTrue(os.path.exists(file_path))

        # Run offline Born-rule probability analyzer
        probs = analyze(level=4, poset_step=1)
        self.assertTrue(len(probs) > 0)
        total_p = sum(info["probability"] for info in probs.values())
        self.assertAlmostEqual(total_p, 1.0, places=5)

    def test_auto_save_and_attractor_discovery(self):
        g = FCRStateGraph("M3_triangle")
        h0 = g.compute_canonical_hash()

        # Check auto-saved state file exists
        saved_file = os.path.join(REPOS_DIR, f"M{g.n}", f"T_0", f"state_{h0}.yaml")
        self.assertTrue(os.path.exists(saved_file))

        # Run automated attractor discovery engine
        res = g.discover_attractors(max_depth=5)
        self.assertGreater(res["branches_visited"], 0)
        self.assertTrue(os.path.exists(os.path.join(REPOS_DIR, "attractors")))

    def test_clock_advance_rules_and_set_restrictions(self):
        g = FCRStateGraph("M3_triangle")
        self.assertEqual(g.time_step, 0)

        # Set allowed at T = 0 and does NOT advance clock
        g.set_edge(0, 1, 1.0, 0.4)
        self.assertEqual(g.time_step, 0)

        # Decay advances clock by 1
        g.decay(0, 1)
        self.assertEqual(g.time_step, 1)

        # Set at T > 0 raises ValueError
        with self.assertRaises(ValueError) as cm:
            g.set_edge(0, 1, 1.0, 0.3)
        self.assertIn("only allowed at T = 0", str(cm.exception))

        # Metric evolve advances clock by 1
        g.metric_evolve(0, 1)
        self.assertEqual(g.time_step, 2)

        # Virtual lock does NOT advance clock (sub-tick phase \Delta T = 0)
        g.virtual_lock_normalize()
        self.assertEqual(g.time_step, 2)

if __name__ == "__main__":
    unittest.main()
