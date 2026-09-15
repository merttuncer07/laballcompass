import unittest

import numpy as np

from capl import learn_portfolio_policy


def data(seed=41):
    rng = np.random.default_rng(seed)
    x1 = rng.normal(size=(180, 2))
    x2 = rng.normal(size=(300, 2))
    def returns(x):
        signal = np.column_stack((.012*x[:, 0], -.012*x[:, 0], .010*x[:, 1]))
        return .0015 + signal + rng.normal(scale=.004, size=signal.shape)
    return x1, returns(x1), x2, returns(x2)


class Tests(unittest.TestCase):
    def test_learned_actions_satisfy_every_constraint(self):
        result = learn_portfolio_policy(*data(), maximum_asset_weight=.7, maximum_turnover=.4,
                                          risk_aversion=2, transaction_cost=.0002,
                                          population_size=40, generations=12, seed=4)
        audit = result.validation_action_audit
        self.assertEqual((audit.sum_violations, audit.lower_bound_violations,
                          audit.upper_bound_violations, audit.turnover_violations), (0, 0, 0, 0))

    def test_policy_improves_untouched_decision_objective(self):
        result = learn_portfolio_policy(*data(), maximum_asset_weight=.7, maximum_turnover=.4,
                                          risk_aversion=2, transaction_cost=.0002,
                                          population_size=60, generations=20, seed=4)
        self.assertGreater(result.validation_objective_improvement_vs_equal_weight, 0)

    def test_result_preserves_all_validation_actions(self):
        values = data()
        result = learn_portfolio_policy(*values, maximum_asset_weight=.7, maximum_turnover=.4,
                                          risk_aversion=2, transaction_cost=.0002,
                                          population_size=30, generations=5, seed=4)
        self.assertEqual(len(result.validation_weights), len(values[2]))
        self.assertEqual(len(result.coefficients), values[0].shape[1] + 1)

    def test_infeasible_weight_cap_is_rejected(self):
        with self.assertRaises(ValueError):
            learn_portfolio_policy(*data(), maximum_asset_weight=.2, maximum_turnover=.4,
                                     risk_aversion=2, transaction_cost=.0002)


if __name__ == "__main__":
    unittest.main()
