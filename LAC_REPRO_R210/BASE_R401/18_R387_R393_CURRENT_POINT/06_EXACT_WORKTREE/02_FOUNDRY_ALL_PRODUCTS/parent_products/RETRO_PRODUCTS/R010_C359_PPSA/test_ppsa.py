import unittest

from ppsa import Release, account_privacy


class PPSATests(unittest.TestCase):
    def test_basic_composition_sums_mechanisms(self) -> None:
        result = account_privacy(
            [Release("a", "MECHANISM", 0.2, 1e-7), Release("b", "MECHANISM", 0.3, 2e-7)],
            epsilon_budget=1.0, delta_budget=1e-6,
        )
        self.assertAlmostEqual(result.reported_epsilon, 0.5)
        self.assertAlmostEqual(result.reported_delta, 3e-7)

    def test_many_small_releases_can_use_advanced_bound(self) -> None:
        releases = [Release(str(i), "MECHANISM", 0.05, 0.0) for i in range(100)]
        result = account_privacy(
            releases, epsilon_budget=3.0, delta_budget=2e-6, advanced_delta_slack=1e-6
        )
        self.assertEqual(result.accounting_method, "ADVANCED_SEQUENTIAL_COMPOSITION")
        self.assertLess(result.reported_epsilon, result.basic_epsilon)
        self.assertTrue(result.within_budget)

    def test_post_processing_costs_no_new_budget(self) -> None:
        result = account_privacy(
            [
                Release("private", "MECHANISM", 0.4, 1e-7),
                Release("chart", "POST_PROCESS", parent_release_id="private"),
                Release("rounded", "POST_PROCESS", parent_release_id="chart"),
            ],
            epsilon_budget=1.0, delta_budget=1e-6,
        )
        self.assertEqual(result.mechanism_count, 1)
        self.assertEqual(result.post_processing_count, 2)
        self.assertAlmostEqual(result.reported_epsilon, 0.4)

    def test_raw_data_access_cannot_claim_post_processing(self) -> None:
        with self.assertRaises(ValueError):
            account_privacy(
                [
                    Release("private", "MECHANISM", 0.4, 0.0),
                    Release("unsafe", "POST_PROCESS", parent_release_id="private", accesses_raw_data=True),
                ],
                epsilon_budget=1.0, delta_budget=1e-6,
            )


if __name__ == "__main__":
    unittest.main()
