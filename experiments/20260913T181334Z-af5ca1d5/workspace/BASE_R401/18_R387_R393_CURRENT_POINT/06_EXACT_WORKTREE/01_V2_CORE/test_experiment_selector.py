import unittest
from experiment_selector import (
    EvidenceRole, ExperimentContract, ExperimentOutcome, TestChannel,
    UncertaintyAxis, choose_next_experiment, apply_outcome, RouteStatus,
)


class ExperimentSelectorTests(unittest.TestCase):
    def contract(self):
        return ExperimentContract(
            decision_id="D1", search_generation=3, selection_round=0,
            axes=(
                UncertaintyAxis("a", "A", 1.0, 1.0, 1.0),
                UncertaintyAxis("b", "B", 0.8, 0.5, 1.0),
            ),
            tests=(
                TestChannel("fast", "Fast", {"a": .4}, 2.0, .9, selection_generation=3, calibration_id='CAL'),
                TestChannel("deep", "Deep", {"a": .9, "b": .5}, 10.0, .95, selection_generation=3, calibration_id='CAL'),
            ),
        )

    def test_selects_progress_per_compute(self):
        plan = choose_next_experiment(self.contract())
        self.assertFalse(plan.stop)
        self.assertEqual(plan.selected_test_id, "fast")

    def test_unknown_calibration_never_gets_fake_score(self):
        c = self.contract()
        c = ExperimentContract(**{**c.__dict__, "tests": c.tests + (TestChannel("unknown","U",{"a":1.0},None,None,selection_generation=3, calibration_id='CAL'),)})
        plan = choose_next_experiment(c)
        route = next(r for r in plan.ranked_routes if r.test_id == "unknown")
        self.assertEqual(route.status, RouteStatus.UNQUANTIFIED)
        self.assertIsNone(route.expected_progress_per_compute)
        self.assertNotEqual(plan.selected_test_id, "unknown")

    def test_protected_validation_never_selected(self):
        c = self.contract()
        protected = TestChannel("pv", "PV", {"a":1.0,"b":1.0}, .01, 1.0, EvidenceRole.PROTECTED_VALIDATION, 3, calibration_id='CAL')
        c = ExperimentContract(**{**c.__dict__, "tests": (protected,) + c.tests})
        plan = choose_next_experiment(c)
        route = next(r for r in plan.ranked_routes if r.test_id == "pv")
        self.assertEqual(route.status, RouteStatus.INELIGIBLE)
        self.assertNotEqual(plan.selected_test_id, "pv")

    def test_blind_axis_reported(self):
        c = ExperimentContract(
            decision_id="D", search_generation=1, selection_round=0,
            axes=(UncertaintyAxis("a","A",1,1), UncertaintyAxis("blind","B",1,1)),
            tests=(TestChannel("t","T",{"a":.5},1,.8,selection_generation=1, calibration_id='CAL'),),
        )
        self.assertEqual(choose_next_experiment(c).blind_axes, ("blind",))

    def test_compute_ceiling(self):
        c = ExperimentContract(
            decision_id="D", search_generation=1, selection_round=0,
            axes=(UncertaintyAxis("a","A",1,1),),
            tests=(TestChannel("too_big","T",{"a":1},11,.9,selection_generation=1, calibration_id='CAL'),),
            compute_ceiling_seconds=10,
        )
        plan = choose_next_experiment(c)
        self.assertTrue(plan.stop)
        self.assertEqual(plan.ranked_routes[0].status, RouteStatus.OVER_COMPUTE_CEILING)

    def test_stop_threshold(self):
        c = ExperimentContract(
            decision_id="D", search_generation=1, selection_round=0,
            axes=(UncertaintyAxis("a","A",.1,.1),), tests=(), stop_unresolved_mass=.02,
        )
        plan = choose_next_experiment(c)
        self.assertTrue(plan.stop)
        self.assertEqual(plan.stop_reason, "DECISION_UNCERTAINTY_BELOW_DECLARED_STOP_THRESHOLD")

    def test_outcome_only_changes_next_round(self):
        c = self.contract()
        plan = choose_next_experiment(c)
        before = c.fingerprint()
        out = ExperimentOutcome("e","D1","fast",3,0,1,{"a":.4})
        nxt = apply_outcome(c, plan, out)
        self.assertEqual(c.fingerprint(), before)
        self.assertEqual(c.selection_round, 0)
        self.assertEqual(nxt.selection_round, 1)
        self.assertEqual(next(a for a in nxt.axes if a.axis_id=="a").uncertainty, .4)
        self.assertNotIn("fast", {t.test_id for t in nxt.tests})

    def test_plan_fingerprint_detects_contract_change(self):
        c = self.contract(); plan = choose_next_experiment(c)
        changed = ExperimentContract(**{**c.__dict__, "stop_unresolved_mass": .1})
        out = ExperimentOutcome("e","D1","fast",3,0,1,{"a":.4})
        with self.assertRaises(ValueError):
            apply_outcome(changed, plan, out)


    def test_unadjusted_backreaction_stays_unquantified(self):
        c = ExperimentContract(
            decision_id="D", search_generation=1, selection_round=0,
            axes=(UncertaintyAxis("a","A",1,1),),
            tests=(TestChannel("t","T",{"a":1},1,.9,selection_generation=1,measurement_backreaction=True,backreaction_adjusted=False,calibration_id="CAL"),),
        )
        plan=choose_next_experiment(c)
        self.assertEqual(plan.ranked_routes[0].status, RouteStatus.UNQUANTIFIED)
        self.assertIn("backreaction_adjustment", plan.ranked_routes[0].unknown_fields)

    def test_protected_outcome_cannot_adapt(self):
        c=self.contract(); plan=choose_next_experiment(c)
        out=ExperimentOutcome("e","D1","fast",3,0,1,{"a":.4},EvidenceRole.PROTECTED_VALIDATION)
        with self.assertRaises(ValueError):
            apply_outcome(c,plan,out)


if __name__ == '__main__': unittest.main()
