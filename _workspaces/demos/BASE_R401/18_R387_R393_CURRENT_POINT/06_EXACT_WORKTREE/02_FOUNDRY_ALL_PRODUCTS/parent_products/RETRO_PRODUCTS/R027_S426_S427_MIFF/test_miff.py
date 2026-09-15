import unittest

from miff import InformationFlow, design_inference_firewall


class Tests(unittest.TestCase):
    def test_minimum_cut_removes_bad_feedback_not_forward_module(self):
        flows = [
            InformationFlow("good", "suspect", .8, 5, "forward"),
            InformationFlow("suspect", "good", .9, 1, "feedback"),
            InformationFlow("good", "decision", .7, 8, "output"),
        ]
        result = design_inference_firewall(
            ["good", "suspect", "decision"], flows,
            suspect_sources=["suspect"], protected_targets=["good", "decision"],
        )
        self.assertEqual(len(result.cut_edges), 1)
        self.assertEqual(result.cut_edges[0].label, "feedback")
        self.assertEqual(result.total_cut_cost, 1)
        self.assertAlmostEqual(result.contamination_reduction_fraction, 1.0)

    def test_unstable_loop_can_be_stabilized_by_cut(self):
        flows = [InformationFlow("good", "bad", 1.2, 4), InformationFlow("bad", "good", 1.0, 1)]
        result = design_inference_firewall(
            ["good", "bad"], flows, suspect_sources=["bad"], protected_targets=["good"]
        )
        self.assertGreaterEqual(result.full_loop_spectral_radius, 1)
        self.assertLess(result.firewalled_loop_spectral_radius, 1)
        self.assertEqual(result.status, "FIREWALL_BREAKS_UNSTABLE_FEEDBACK")

    def test_unconnected_suspect_requires_no_cut(self):
        result = design_inference_firewall(
            ["good", "bad", "report"], [InformationFlow("good", "report", .5, 1)],
            suspect_sources=["bad"], protected_targets=["good"],
        )
        self.assertEqual(result.cut_edges, ())
        self.assertEqual(result.status, "NO_SUSPECT_TO_PROTECTED_PATH")

    def test_undeclared_module_is_rejected(self):
        with self.assertRaises(ValueError):
            design_inference_firewall(
                ["a", "b"], [InformationFlow("a", "c", .2)],
                suspect_sources=["a"], protected_targets=["b"],
            )


if __name__ == "__main__":
    unittest.main()
