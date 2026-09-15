import tempfile, unittest
from pathlib import Path

from experiment_selector import (
    EvidenceRole, ExperimentContract, ExperimentOutcome, TestChannel, UncertaintyAxis,
    choose_next_experiment,
)
from experiment_telemetry import (
    ExperimentRunRecord, ExperimentTelemetryLedger, compile_calibration_snapshot,
    hydrate_contract_from_calibration, record_from_round,
)


def ev(i, *, gen=1, release_gen=1, shell='S', role=EvidenceRole.DEVELOPMENT,
       eligible=True, before=1.0, after=.5, compute=2.0,
       backreaction=False, adjusted=False, valid=True, status='COMPLETE', sig='SIG'):
    return ExperimentRunRecord(
        event_id=f'e{i}', decision_id=f'd{i}', test_id='T', test_signature=sig,
        problem_shell=shell, shell_tags=(), search_generation=gen, selection_round=0,
        release_generation=release_gen, release_round=1, contract_fingerprint=f'fp{i}',
        evidence_role=role, calibration_eligible=eligible,
        measurement_backreaction=backreaction, backreaction_adjusted=adjusted,
        before_uncertainty_by_axis={'x':before}, after_uncertainty_by_axis={'x':after},
        compute_seconds=compute, run_status=status, measurement_valid=valid,
    )


def contract(gen=2, shell='S', sig='SIG'):
    return ExperimentContract(
        decision_id='D', search_generation=gen, selection_round=0, problem_shell=shell,
        axes=(UncertaintyAxis('x','x',1.0,1.0),),
        tests=(TestChannel('T','T',{'x':None},None,None,selection_generation=gen,test_signature=sig),),
    )


class ExperimentTelemetryTests(unittest.TestCase):
    def test_same_generation_and_protected_never_calibrate(self):
        rows=[ev(i) for i in range(5)]
        rows += [ev(10,gen=2,release_gen=2), ev(11,role=EvidenceRole.PROTECTED_VALIDATION)]
        snap=compile_calibration_snapshot(rows,target_generation=2,problem_shell='S')
        self.assertEqual(snap.calibrations[0].attempt_count,5)
        self.assertEqual(snap.excluded_global_counts['same_or_future_generation'],1)
        self.assertEqual(snap.excluded_global_counts['protected_validation'],1)

    def test_insufficient_support_stays_unknown(self):
        snap=compile_calibration_snapshot([ev(i) for i in range(4)],target_generation=2,problem_shell='S')
        c=snap.calibrations[0]
        self.assertIsNone(c.reliability_lower_bound)
        self.assertIsNone(c.compute_upper_seconds)
        self.assertIsNone(c.expected_resolution_lower_by_axis['x'])
        hydrated=hydrate_contract_from_calibration(contract(),snap)
        self.assertIsNone(hydrated.tests[0].reliability)
        self.assertIsNone(hydrated.tests[0].compute_seconds)
        self.assertIsNone(hydrated.tests[0].expected_resolution_by_axis['x'])
        self.assertIsNone(choose_next_experiment(hydrated).selected_test_id)

    def test_prior_generation_telemetry_unlocks_future_routing(self):
        rows=[ev(i,after=.45 + .01*(i%2),compute=2.0+.1*i) for i in range(6)]
        snap=compile_calibration_snapshot(rows,target_generation=2,problem_shell='S')
        hydrated=hydrate_contract_from_calibration(contract(),snap)
        t=hydrated.tests[0]
        self.assertIsNotNone(t.reliability)
        self.assertGreater(t.reliability,0)
        self.assertEqual(t.compute_seconds,max(e.compute_seconds for e in rows))
        self.assertGreater(t.expected_resolution_by_axis['x'],0)
        self.assertTrue(t.calibration_id.startswith('AUTO_R5:'))
        self.assertEqual(choose_next_experiment(hydrated).selected_test_id,'T')

    def test_exact_shell_and_signature_only(self):
        rows=[ev(i,shell='S',sig='SIG') for i in range(5)]
        snap=compile_calibration_snapshot(rows,target_generation=2,problem_shell='S')
        wrong_sig=hydrate_contract_from_calibration(contract(sig='OTHER'),snap)
        self.assertIsNone(wrong_sig.tests[0].reliability)
        with self.assertRaises(ValueError):
            hydrate_contract_from_calibration(contract(shell='OTHER'),snap)

    def test_unadjusted_backreaction_is_unusable_and_penalizes_reliability(self):
        rows=[ev(i) for i in range(5)] + [ev(9,backreaction=True,adjusted=False)]
        snap=compile_calibration_snapshot(rows,target_generation=2,problem_shell='S')
        c=snap.calibrations[0]
        self.assertEqual(c.attempt_count,6)
        self.assertEqual(c.usable_count,5)
        self.assertEqual(c.excluded_counts['unadjusted_backreaction'],1)
        perfect=compile_calibration_snapshot([ev(i) for i in range(6)],target_generation=2,problem_shell='S').calibrations[0]
        self.assertLess(c.reliability_lower_bound,perfect.reliability_lower_bound)

    def test_record_from_frozen_round_captures_before_after(self):
        c=ExperimentContract(
            decision_id='D',search_generation=1,selection_round=0,problem_shell='S',
            axes=(UncertaintyAxis('x','x',1,1),),
            tests=(TestChannel('T','T',{'x':.5},1,1,selection_generation=1,calibration_id='MANUAL',test_signature='SIG'),),
        )
        plan=choose_next_experiment(c)
        outcome=ExperimentOutcome('o','D','T',1,0,1,{'x':.4})
        e=record_from_round(c,plan,outcome,event_id='run1',compute_seconds=1.2,calibration_eligible=True)
        self.assertEqual(e.contract_fingerprint,c.fingerprint())
        self.assertEqual(e.before_uncertainty_by_axis['x'],1)
        self.assertEqual(e.after_uncertainty_by_axis['x'],.4)
        self.assertEqual(e.test_signature,'SIG')

    def test_snapshot_is_deterministic(self):
        rows=[ev(i) for i in range(5)]
        a=compile_calibration_snapshot(rows,target_generation=2,problem_shell='S')
        b=compile_calibration_snapshot(list(reversed(rows)),target_generation=2,problem_shell='S')
        self.assertEqual(a.fingerprint,b.fingerprint)

    def test_jsonl_ledger_rejects_duplicate_event(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'events.jsonl'; ledger=ExperimentTelemetryLedger(); e=ev(1)
            ledger.append_jsonl(p,e)
            with self.assertRaises(ValueError): ledger.append_jsonl(p,e)


if __name__=='__main__': unittest.main()
