import unittest

import numpy as np

if __package__:
    from .dari import DesignAwareRandomizationInference
else:
    from dari import DesignAwareRandomizationInference


def fixture():
    rng = np.random.default_rng(17)
    x = rng.normal(size=(48, 3))
    engine = DesignAwareRandomizationInference()
    design = engine.design(
        x,
        treated_count=24,
        randomization_draws=1000,
        acceptance_fraction=0.1,
        seed=23,
    )
    z = np.asarray(design.certificate.assignment)
    y = 1.5 * z + 0.15 * x[:, 0] + rng.normal(scale=0.08, size=len(x))
    return engine, x, z, y, design


class DARITests(unittest.TestCase):
    def test_cbacs_realized_assignment_is_in_exact_pool(self):
        _, _, z, _, design = fixture()
        self.assertEqual(len(design.accepted_assignments), 100)
        self.assertTrue(any(np.array_equal(z, row) for row in design.accepted_assignments))

    def test_false_zero_rejected_and_true_effect_retained(self):
        engine, _, z, y, design = fixture()
        false_zero = engine.randomization_test(y, z, design.accepted_assignments, null_effect=0.0)
        true_effect = engine.randomization_test(y, z, design.accepted_assignments, null_effect=1.5)
        self.assertLessEqual(false_zero.two_sided_p_value, 0.05)
        self.assertGreater(true_effect.two_sided_p_value, 0.05)

    def test_inverted_confidence_set_contains_true_effect(self):
        engine, _, z, y, design = fixture()
        result = engine.confidence_set(
            y,
            z,
            design.accepted_assignments,
            np.linspace(0.0, 2.5, 26),
        )
        self.assertIn(1.5, result["accepted_effects"])
        self.assertNotIn(0.0, result["accepted_effects"])

    def test_ote_is_reported_as_separate_model_assisted_estimate(self):
        engine, x, z, y, _ = fixture()
        estimate = engine.orthogonal_point_estimate(x, z, y, folds=4, seed=9)
        self.assertAlmostEqual(estimate.target, 1.5, delta=0.2)
        self.assertGreater(estimate.standard_error, 0.0)


if __name__ == "__main__":
    unittest.main()
