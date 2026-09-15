import unittest

from mlhpe import audit_three_lists, chapman_two_list


class MLHPETests(unittest.TestCase):
    def test_chapman_estimate_is_bias_corrected(self) -> None:
        result = chapman_two_list(100, 80, 40)
        self.assertAlmostEqual(result.population_estimate, (101 * 81 / 41) - 1)
        self.assertGreater(result.standard_error, 0)

    def test_independence_and_pairwise_surface_is_complete(self) -> None:
        counts = {"001": 30, "010": 25, "011": 10, "100": 35, "101": 12, "110": 15, "111": 8}
        result = audit_three_lists(counts)
        self.assertEqual(len(result.models), 8)
        self.assertEqual(result.observed_population, 135)

    def test_saturated_model_is_flagged(self) -> None:
        counts = {"001": 30, "010": 25, "011": 10, "100": 35, "101": 12, "110": 15, "111": 8}
        result = audit_three_lists(counts)
        saturated = next(item for item in result.models if len(item.interactions) == 3)
        self.assertEqual(saturated.residual_degrees_of_freedom, 0)
        self.assertEqual(saturated.status, "SATURATED_OBSERVED_TABLE")
        self.assertEqual(saturated.akaike_weight, 0.0)
        self.assertTrue(result.saturated_models_excluded_from_selection)

    def test_dependence_changes_hidden_population_estimate(self) -> None:
        counts = {"100": 120, "010": 100, "001": 160, "110": 90, "101": 35, "011": 30, "111": 45}
        result = audit_three_lists(counts)
        totals = [item.total_population_estimate for item in result.models]
        self.assertGreater(max(totals) - min(totals), 20.0)


if __name__ == "__main__":
    unittest.main()
