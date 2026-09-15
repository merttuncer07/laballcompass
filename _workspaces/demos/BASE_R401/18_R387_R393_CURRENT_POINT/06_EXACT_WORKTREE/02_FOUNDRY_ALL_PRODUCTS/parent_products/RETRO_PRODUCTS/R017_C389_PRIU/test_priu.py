import unittest

from priu import Claim, Scenario, audit_priority_reset


class PRIUTests(unittest.TestCase):
    def setUp(self) -> None:
        self.claims = [Claim("SENIOR", 80.0), Claim("JUNIOR", 80.0)]
        self.states = [
            Scenario(0.2, 40.0, 60.0),
            Scenario(0.5, 40.0, 130.0),
            Scenario(0.3, 40.0, 220.0),
        ]

    def test_superpriority_unlocks_positive_value_investment(self) -> None:
        result = audit_priority_reset(
            self.claims, self.states, new_money_principal=30.0, promised_new_money_repayment=33.0
        )
        senior = result.arrangements[0]
        self.assertTrue(senior.financing_unlocked)
        self.assertAlmostEqual(senior.expected_new_money_recovery, 33.0)
        self.assertAlmostEqual(senior.enterprise_incremental_value_net_of_funding, 73.0)

    def test_junior_new_money_remains_blocked(self) -> None:
        result = audit_priority_reset(
            self.claims, self.states, new_money_principal=30.0, promised_new_money_repayment=33.0
        )
        self.assertFalse(result.arrangements[-1].financing_unlocked)
        self.assertEqual(result.least_disruptive_unlocking_position, 0)

    def test_existing_claimants_can_be_protected(self) -> None:
        result = audit_priority_reset(
            self.claims, self.states, new_money_principal=30.0, promised_new_money_repayment=33.0
        )
        self.assertTrue(result.arrangements[0].all_existing_claims_protected)
        self.assertIn(0, result.protected_unlocking_positions)

    def test_probability_validation(self) -> None:
        with self.assertRaises(ValueError):
            audit_priority_reset(
                self.claims,
                [Scenario(0.4, 20.0, 100.0), Scenario(0.4, 20.0, 100.0)],
                new_money_principal=10.0,
                promised_new_money_repayment=11.0,
            )


if __name__ == "__main__":
    unittest.main()
