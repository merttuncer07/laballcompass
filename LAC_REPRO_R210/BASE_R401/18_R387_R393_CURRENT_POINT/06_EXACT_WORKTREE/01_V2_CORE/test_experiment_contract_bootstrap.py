import json
import unittest
from pathlib import Path

from experiment_contract_bootstrap import (
    audit_queue_bootstrap_readiness,
    bootstrap_queue_row,
    compile_bootstrap_and_route,
    discover_existing_composition_suites,
    run_fixed_suite_pilot,
)

ROOT=Path(__file__).resolve().parent
QUEUE=json.loads((ROOT/'generated_v2_foundry'/'CORE_V2_FOUNDRY_COMPOSITION_QUEUE.json').read_text())


class ExperimentContractBootstrapTests(unittest.TestCase):
    def test_discovers_completed_composition_suites(self):
        suites=discover_existing_composition_suites(ROOT)
        self.assertIn(('LCB-K048','FOUNDRY:P136'),suites)
        self.assertGreaterEqual(len(suites[('LCB-K048','FOUNDRY:P136')].cases),5)
        self.assertIn(('LCB-K048','FOUNDRY:P144'),suites)
        self.assertIn(('LCB-K081','FOUNDRY:P138'),suites)
        self.assertEqual(len(suites[('LCB-K081','FOUNDRY:P138')].cases),13)
        self.assertIn(('LCB-K019','FOUNDRY:P003'),suites)
        self.assertEqual(len(suites[('LCB-K019','FOUNDRY:P003')].cases),12)
        self.assertIn(('LCB-K068','FOUNDRY:P025'),suites)
        self.assertEqual(len(suites[('LCB-K068','FOUNDRY:P025')].cases),12)
        expected=len([d for d in (ROOT/'products').glob('V2P*') if (d/'COMPOSITION.json').exists() and list(d.glob('test_*.py'))])
        self.assertEqual(len(suites),expected)

    def test_nonmatching_queue_row_remains_unquantified(self):
        row=next(r for r in QUEUE if (r['supplier_id'],r['consumer_id']) not in discover_existing_composition_suites(ROOT))
        d=bootstrap_queue_row(row,root=ROOT)
        self.assertIn(d.status,{'ADAPTER_REQUIRED_CONSUMER_INVARIANT_SUITE_AVAILABLE','SUPPLIER_INVARIANT_SUITE_AVAILABLE_NO_COMPOSITION_HARNESS','NO_EXECUTABLE_TEST_SURFACE_DISCOVERED'})
        self.assertIsNone(d.contract)

    def test_bootstrap_preserves_structural_questions_but_only_quantifies_coverage(self):
        row=next(r for r in QUEUE if r['supplier_id']=='LCB-K048' and r['consumer_id']=='FOUNDRY:P136')
        d=bootstrap_queue_row(row,root=ROOT)
        self.assertEqual(d.status,'FIXED_PILOT_SCHEDULE_AVAILABLE')
        self.assertTrue(d.structural_questions)
        self.assertTrue(all(q['numeric_uncertainty']=='UNKNOWN' for q in d.structural_questions))
        self.assertEqual([a.axis_id for a in d.contract.axes],['declared_executable_contract_case_coverage'])
        t=d.contract.tests[0]
        self.assertIsNone(t.reliability); self.assertIsNone(t.compute_seconds)
        self.assertIsNone(t.expected_resolution_by_axis['declared_executable_contract_case_coverage'])

    def test_real_fixed_suite_pilot_unlocks_later_generation_only(self):
        row=next(r for r in QUEUE if r['supplier_id']=='LCB-K048' and r['consumer_id']=='FOUNDRY:P136')
        d=bootstrap_queue_row(row,root=ROOT,search_generation=0)
        events=run_fixed_suite_pilot(d,release_generation=1)
        self.assertEqual(len(events),6)
        self.assertTrue(all(e.run_status=='COMPLETE' for e in events))
        future,hydrated,snapshot,plan=compile_bootstrap_and_route(d,events,target_generation=2)
        self.assertEqual(snapshot.calibrations[0].attempt_count,6)
        self.assertIsNotNone(hydrated.tests[0].reliability)
        self.assertIsNotNone(hydrated.tests[0].compute_seconds)
        self.assertGreater(hydrated.tests[0].expected_resolution_by_axis['declared_executable_contract_case_coverage'],0)
        self.assertEqual(plan.selected_test_id,d.suite.test_id)
        self.assertEqual(future.search_generation,2)

    def test_queue_audit_is_explicit(self):
        a=audit_queue_bootstrap_readiness(QUEUE,root=ROOT)
        self.assertEqual(a['queue_rows'],1000)
        self.assertGreaterEqual(a['pilotable_existing_suite_rows'],1)
        self.assertEqual(a['pilotable_existing_suite_rows']+a['not_pilotable_existing_suite_rows'],1000)
        self.assertEqual(a['foundry_component_test_surfaces'],145)
        self.assertEqual(sum(a['status_counts'].values()),1000)


if __name__=='__main__': unittest.main()
