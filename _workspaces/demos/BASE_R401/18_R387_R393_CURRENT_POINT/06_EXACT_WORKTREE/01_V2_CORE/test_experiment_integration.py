import json, unittest
from pathlib import Path
from core_v2 import choose_lab_next_experiment, audit_foundry_experiment_readiness
from search_to_foundry import build_packet

ROOT=Path(__file__).resolve().parent

class ExperimentIntegrationTests(unittest.TestCase):
    def test_core_entry_point(self):
        c={
            'decision_id':'D','search_generation':1,'selection_round':0,
            'axes':[{'axis_id':'x','uncertainty':1,'decision_leverage':1}],
            'tests':[{'test_id':'t','expected_resolution_by_axis':{'x':.5},'compute_seconds':1,'reliability':1,'selection_generation':1,'calibration_id':'CAL'}],
        }
        self.assertEqual(choose_lab_next_experiment(c).selected_test_id,'t')

    def test_current_queue_is_not_ready_without_telemetry(self):
        a=audit_foundry_experiment_readiness()
        self.assertEqual(a['queue_rows'],1000)
        self.assertEqual(a['ready_rows'],0)

    def test_foundry_packet_exposes_not_ready_gate(self):
        problem=json.loads((ROOT/'generated_search'/'EXAMPLE_PROBLEM_CONTRACT_CRYPTO_V1.json').read_text())
        packet=build_packet(problem,capability_k=3,primitive_k=3,expansion_seeds=1,suppliers_per_seed=1,incremental=False)
        self.assertEqual(packet['engine'],'LABALLCOMPASS_SEARCH_TO_FOUNDRY_R12')
        self.assertEqual(packet['experiment_selection']['status'],'NOT_READY_WITHOUT_DECLARED_EXPERIMENT_CONTRACT')

    def test_foundry_packet_routes_declared_contract(self):
        problem=json.loads((ROOT/'generated_search'/'EXAMPLE_PROBLEM_CONTRACT_CRYPTO_V1.json').read_text())
        problem['experiment_contract']={
            'decision_id':'D','search_generation':1,'selection_round':0,
            'axes':[{'axis_id':'x','uncertainty':1,'decision_leverage':1}],
            'tests':[{'test_id':'t','expected_resolution_by_axis':{'x':.5},'compute_seconds':2,'reliability':1,'selection_generation':1,'calibration_id':'CAL'}],
        }
        packet=build_packet(problem,capability_k=2,primitive_k=2,expansion_seeds=1,suppliers_per_seed=1,incremental=False)
        self.assertEqual(packet['experiment_selection']['status'],'ROUTED_FROM_DECLARED_CONTRACT')
        self.assertEqual(packet['experiment_selection']['plan']['selected_test_id'],'t')

    def test_foundry_packet_routes_from_prior_generation_telemetry(self):
        from experiment_telemetry import ExperimentRunRecord, compile_calibration_snapshot
        from experiment_selector import EvidenceRole
        problem=json.loads((ROOT/'generated_search'/'EXAMPLE_PROBLEM_CONTRACT_CRYPTO_V1.json').read_text())
        problem['experiment_contract']={
            'decision_id':'D','search_generation':2,'selection_round':0,'problem_shell':'CRYPTO_TEST',
            'axes':[{'axis_id':'x','uncertainty':1,'decision_leverage':1}],
            'tests':[{'test_id':'t','test_signature':'SIG:v1','expected_resolution_by_axis':{'x':None},'compute_seconds':None,'reliability':None,'selection_generation':2}],
        }
        rows=[]
        for i in range(5):
            rows.append(ExperimentRunRecord(
                event_id=f'e{i}',decision_id=f'old{i}',test_id='t',test_signature='SIG:v1',problem_shell='CRYPTO_TEST',shell_tags=(),
                search_generation=1,selection_round=0,release_generation=1,release_round=1,contract_fingerprint=f'fp{i}',
                evidence_role=EvidenceRole.DEVELOPMENT,calibration_eligible=True,measurement_backreaction=False,backreaction_adjusted=False,
                before_uncertainty_by_axis={'x':1.0},after_uncertainty_by_axis={'x':0.4},compute_seconds=2.0,
            ))
        snap=compile_calibration_snapshot(rows,target_generation=2,problem_shell='CRYPTO_TEST')
        packet=build_packet(problem,capability_k=2,primitive_k=2,expansion_seeds=1,suppliers_per_seed=1,incremental=False,experiment_calibration_snapshot=snap)
        self.assertEqual(packet['experiment_selection']['status'],'ROUTED_FROM_FROZEN_AUTO_CALIBRATION')
        self.assertEqual(packet['experiment_selection']['plan']['selected_test_id'],'t')
        self.assertEqual(packet['experiment_selection']['calibration_snapshot_fingerprint'],snap.fingerprint)

    def test_search_packet_surfaces_existing_bootstrap_pilot(self):
        problem={
            'problem_id':'R6_P136_BOOTSTRAP',
            'objective':'quasineutral measurement acquisition information decision channel uncertainty cost',
            'mechanism_needs':['measurement','decision','uncertainty'],
        }
        packet=build_packet(problem,capability_k=12,primitive_k=3,expansion_seeds=8,suppliers_per_seed=8,incremental=False)
        hits=[x for x in packet['experiment_bootstrap_opportunities'] if x['supplier_id']=='LCB-K048' and x['consumer_id']=='FOUNDRY:P136']
        self.assertTrue(hits)
        hit=hits[0]
        self.assertEqual(hit['product_id'],'V2P002')
        self.assertEqual(hit['case_count'],6)
        self.assertIn('NUMERIC_ROUTING_STILL_UNKNOWN',hit['status'])

    def test_search_packet_surfaces_r7_adapter_bootstrap_pilot(self):
        problem={
            'problem_id':'R7_P144_BOOTSTRAP',
            'objective':'persistence stability identification experiment acquisition uncertainty fidelity budget correlation',
            'mechanism_needs':['dynamics','measurement','decision','allocation','uncertainty'],
        }
        packet=build_packet(problem,capability_k=20,primitive_k=3,expansion_seeds=12,suppliers_per_seed=8,incremental=False)
        hits=[x for x in packet['experiment_bootstrap_opportunities'] if x['supplier_id']=='LCB-K048' and x['consumer_id']=='FOUNDRY:P144']
        self.assertTrue(hits)
        hit=hits[0]
        self.assertEqual(hit['product_id'],'V2P003')
        self.assertEqual(hit['case_count'],12)
        self.assertIn('NUMERIC_ROUTING_STILL_UNKNOWN',hit['status'])

    def test_search_packet_surfaces_r8_observation_policy_adapter(self):
        problem={
            'problem_id':'R8_P138_BOOTSTRAP',
            'objective':'search policy information acquisition observation policy confounding measurement backaction passive state proxy target belief',
            'mechanism_needs':['measurement','decision','uncertainty','causal','control'],
        }
        packet=build_packet(problem,capability_k=24,primitive_k=3,expansion_seeds=16,suppliers_per_seed=10,incremental=False)
        hits=[x for x in packet['experiment_bootstrap_opportunities'] if x['supplier_id']=='LCB-K081' and x['consumer_id']=='FOUNDRY:P138']
        self.assertEqual(len(hits),1)
        hit=hits[0]
        self.assertEqual(hit['product_id'],'V2P004')
        self.assertEqual(hit['case_count'],12)
        self.assertIn('NUMERIC_ROUTING_STILL_UNKNOWN',hit['status'])

if __name__=='__main__': unittest.main()
