import unittest

if __package__:
    from .dpcg import GlobalPrivateDecisionCoordinator
else:
    from dpcg import GlobalPrivateDecisionCoordinator
if __package__:
    from .parents.dtpr import DecisionSpec, DecisionTargetedPrivateRelease
else:
    from parents.dtpr import DecisionSpec, DecisionTargetedPrivateRelease


def spec(name):
    return DecisionSpec(name, (0.0,), ("LOW", "HIGH"), sensitivity=1.0)


class DPCGTests(unittest.TestCase):
    def test_global_budget_prevents_local_overspend(self):
        global_account = GlobalPrivateDecisionCoordinator(epsilon_budget=1.5)
        a = DecisionTargetedPrivateRelease(1.0, seed=1)
        b = DecisionTargetedPrivateRelease(1.0, seed=2)
        global_account.release_action(
            release_id="desk_a:risk", controller=a, spec=spec("a"), true_score=1.0, epsilon=0.8
        )
        before = b.remaining_epsilon
        with self.assertRaises(RuntimeError):
            global_account.release_action(
                release_id="desk_b:risk", controller=b, spec=spec("b"), true_score=1.0, epsilon=0.8
            )
        self.assertEqual(b.remaining_epsilon, before)

    def test_post_processing_is_zero_cost(self):
        coordinator = GlobalPrivateDecisionCoordinator(epsilon_budget=1.5)
        controller = DecisionTargetedPrivateRelease(1.0, seed=1)
        coordinator.release_action(
            release_id="desk_a:risk", controller=controller, spec=spec("a"), true_score=1.0, epsilon=0.8
        )
        coordinator.add_post_process(
            release_id="desk_a:risk:label", parent_release_id="desk_a:risk"
        )
        account = coordinator.account()
        self.assertAlmostEqual(account.reported_epsilon, 0.8)
        self.assertEqual(account.post_processing_count, 1)

    def test_two_allowed_releases_compose_globally(self):
        coordinator = GlobalPrivateDecisionCoordinator(epsilon_budget=1.5)
        a = DecisionTargetedPrivateRelease(1.0, seed=1)
        b = DecisionTargetedPrivateRelease(1.0, seed=2)
        coordinator.release_action(release_id="a", controller=a, spec=spec("a"), true_score=1, epsilon=0.8)
        coordinator.release_action(release_id="b", controller=b, spec=spec("b"), true_score=1, epsilon=0.6)
        account = coordinator.account()
        self.assertAlmostEqual(account.reported_epsilon, 1.4)
        self.assertTrue(account.within_budget)

    def test_duplicate_release_id_rejected(self):
        coordinator = GlobalPrivateDecisionCoordinator(epsilon_budget=2.0)
        controller = DecisionTargetedPrivateRelease(2.0, seed=1)
        coordinator.release_action(release_id="a", controller=controller, spec=spec("a"), true_score=1, epsilon=0.5)
        with self.assertRaises(ValueError):
            coordinator.release_action(release_id="a", controller=controller, spec=spec("a"), true_score=1, epsilon=0.5)


if __name__ == "__main__":
    unittest.main()
