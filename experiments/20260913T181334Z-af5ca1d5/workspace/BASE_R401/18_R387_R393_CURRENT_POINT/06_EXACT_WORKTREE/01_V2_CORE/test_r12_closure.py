from __future__ import annotations
import csv, json, tempfile, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parent

class TelemetryPersistenceTests(unittest.TestCase):
    def test_canonical_runtime_event_survives_registry_refresh(self):
        import tempfile
        from experiment_telemetry import ExperimentRunRecord, ExperimentTelemetryLedger
        from experiment_selector import EvidenceRole
        from telemetry_registry import write_registry
        with tempfile.TemporaryDirectory() as td:
            core=Path(td)
            (core/'search_data').mkdir(parents=True)
            (core/'generated_search').mkdir(parents=True)
            (core/'generated').mkdir(parents=True)
            (core/'generated'/'core_registry_raw.json').write_bytes((ROOT/'generated'/'core_registry_raw.json').read_bytes())
            event=ExperimentRunRecord(
                event_id='MISSION::persist',decision_id='D',test_id='T',test_signature='SIG',
                problem_shell='MISSION_SHELL',shell_tags=('MISSION',),search_generation=1,selection_round=0,
                release_generation=2,release_round=1,contract_fingerprint='FP',evidence_role=EvidenceRole.DEVELOPMENT,
                calibration_eligible=True,measurement_backreaction=False,backreaction_adjusted=False,
                before_uncertainty_by_axis={'x':1.0},after_uncertainty_by_axis={'x':0.5},compute_seconds=1.0)
            ledger=core/'search_data'/'EXPERIMENT_TELEMETRY.jsonl'
            ExperimentTelemetryLedger().append_jsonl(ledger,event)
            out,_,idx=write_registry(core)
            events=ExperimentTelemetryLedger.load_jsonl(out).events
            self.assertEqual([e.event_id for e in events],['MISSION::persist'])
            self.assertEqual(idx['event_count'],1)

class TelemetryClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index=json.loads((ROOT/'generated_search'/'EXPERIMENT_TELEMETRY_INDEX_R12.json').read_text())
        cls.queue=json.loads((ROOT/'generated_v2_foundry'/'CORE_V2_FOUNDRY_COMPOSITION_QUEUE.json').read_text())

    def test_all_current_bootstrap_events_match_current_suites(self):
        self.assertGreater(self.index['event_count'],0)
        self.assertEqual(self.index['exact_current_suite_matches'],self.index['event_count'])
        self.assertEqual(self.index['unmatched_event_count'],0)

    def test_all_completed_suites_are_calibrated(self):
        expected=len([d for d in (ROOT/'products').glob('V2P*') if (d/'COMPOSITION.json').exists() and list(d.glob('test_*.py'))])
        self.assertEqual(self.index['current_completed_suite_count'],expected)
        self.assertEqual(self.index['calibrated_current_suite_count'],expected)
        self.assertTrue(all(x['status']=='CALIBRATED_EXACT_SHELL' for x in self.index['calibration_by_edge'].values()))

    def test_queue_is_hydrated_from_canonical_telemetry(self):
        known=[r for r in self.queue if r.get('experiment_bootstrap_status')=='FIXED_PILOT_SCHEDULE_AVAILABLE']
        self.assertEqual(len(known),self.index['current_completed_suite_count'])
        self.assertTrue(all(r['experiment_telemetry_status']=='STANDARDIZED_TELEMETRY_AVAILABLE' for r in known))
        self.assertTrue(all(r['experiment_calibration_status']=='CALIBRATED_EXACT_SHELL' for r in known))
        self.assertTrue(all(r['experiment_telemetry_event_count']==r['experiment_bootstrap_case_count'] for r in known))

class InteractionMapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.obj=json.loads((ROOT/'generated_search'/'INTERACTION_MAP_R12.json').read_text())
        cls.edges=cls.obj['edges']

    def test_completed_rejected_and_hypothesis_are_distinct(self):
        counts=self.obj['relation_counts']
        self.assertEqual(counts['COMPLETED_COMPOSITION'],json.loads((ROOT/'generated_search'/'EXPERIMENT_TELEMETRY_INDEX_R12.json').read_text())['current_completed_suite_count'])
        rejected=json.loads((ROOT/'generated_v2_foundry'/'CORE_V2_FOUNDRY_REJECTED_EDGES.json').read_text())
        self.assertEqual(counts['REJECTED_CURRENT_INTERFACE'],len(rejected))
        self.assertEqual(counts.get('CURATED_HYPOTHESIS',0),0)
        self.assertGreaterEqual(counts['PARENT_OF'],50)

    def test_rejected_edges_are_inactive_but_preserved(self):
        e=next(x for x in self.edges if x['source_id']=='LCB-K087' and x['target_id']=='FOUNDRY:P002' and x['relation']=='REJECTED_CURRENT_INTERFACE')
        self.assertFalse(e['active'])
        self.assertTrue(e['rationale'])

    def test_completed_edge_carries_product_and_telemetry(self):
        e=next(x for x in self.edges if x['source_id']=='LCB-K009' and x['target_id']=='FOUNDRY:P026' and x['relation']=='COMPLETED_COMPOSITION')
        self.assertEqual(e['product_id'],'V2P007')
        self.assertEqual(e['telemetry_events'],12)


    def test_interaction_map_covers_every_search_node_without_inventing_edges(self):
        obj=json.loads((ROOT/'generated_search'/'INTERACTION_MAP_R12.json').read_text())
        self.assertEqual(obj['node_counts'].get('CAPABILITY'),310)
        self.assertEqual(obj['node_counts'].get('PRIMITIVE'),4000)
        self.assertEqual(obj['node_count'],4310)
        # Primitive provenance is carried on the node; no synthetic primitive-to-primitive
        # interaction is created merely to make the graph dense.
        primitive_nodes=[n for n in obj['nodes'] if n['node_type']=='PRIMITIVE']
        self.assertTrue(all(n.get('primitive') and n.get('constraint_shell') for n in primitive_nodes))
        self.assertTrue(all(n.get('provenance',{}).get('source_concept') for n in primitive_nodes))

    def test_parent_provenance_products_are_all_mapped(self):
        products={x['target_id'] for x in self.edges if x['relation']=='PARENT_OF'}
        provenance_files=list((ROOT.parent/'02_FOUNDRY_ALL_PRODUCTS'/'products').glob('P*/PARENT_PROVENANCE.md'))
        expected={'FOUNDRY:'+p.parent.name.split('_',1)[0] for p in provenance_files}
        self.assertEqual(products,expected)

    def test_inferred_candidates_do_not_enter_search_adjacency(self):
        from interaction_map import load_interaction_map, INFERRED
        m=load_interaction_map(ROOT/'generated_search'/'INTERACTION_MAP_R12.json')
        adj=m.search_adjacency()
        inferred=next(x for x in self.edges if x['relation']==INFERRED)
        self.assertNotEqual(adj.get(inferred['target_id'],{}).get(inferred['source_id']), 1.0)
        # If same pair also has an explicit relation it may exist; otherwise it must be absent.
        explicit=any(x['source_id']==inferred['source_id'] and x['target_id']==inferred['target_id'] and x['relation'] in {'COMPLETED_COMPOSITION','CURATED_HYPOTHESIS'} for x in self.edges)
        if not explicit:
            self.assertNotIn(inferred['source_id'],adj.get(inferred['target_id'],{}))

class SimpleLexiconTests(unittest.TestCase):
    def test_identity_ignores_domain_and_source_label(self):
        from simple_lexicon import canonical_mechanism_id
        a={'primitive':'Move a tiny amount; see how much the other thing moves','constraint_shell':'Limit must exist','domain':'Math','source_concept':'Derivative'}
        b={**a,'domain':'Finance','source_concept':'Price sensitivity'}
        self.assertEqual(canonical_mechanism_id(a),canonical_mechanism_id(b))

    def test_corpus_primitive_text_is_simple_and_provenance_is_separate(self):
        rows=[json.loads(x) for x in (ROOT/'generated_search'/'LAB_SEARCH_CORPUS.jsonl').read_text().splitlines() if x.strip()]
        d=next(x for x in rows if x['document_id']=='PRIMITIVE:M-001')
        self.assertIn('Move a tiny amount',d['text'])
        self.assertNotIn('Derivative',d['text'])
        self.assertEqual(d['metadata']['source_concept'],'Derivative')
        self.assertIn('Derivative',d['metadata']['search_aliases'])

class CampaignMemoryTests(unittest.TestCase):
    def test_current_memory_does_not_fake_empirical_learning(self):
        rows=[json.loads(x) for x in (ROOT/'search_data'/'CAMPAIGN_MEMORY.jsonl').read_text().splitlines() if x.strip()]
        suite_count=json.loads((ROOT/'generated_search'/'EXPERIMENT_TELEMETRY_INDEX_R12.json').read_text())['current_completed_suite_count']
        rejected_count=len(json.loads((ROOT/'generated_v2_foundry'/'CORE_V2_FOUNDRY_REJECTED_EDGES.json').read_text()))
        self.assertEqual(len(rows),suite_count+rejected_count)
        self.assertEqual(sum(bool(r['learning_eligible']) for r in rows),0)
        self.assertEqual(sum(r['outcome']=='REJECTED_CURRENT_INTERFACE' for r in rows),rejected_count)
        self.assertEqual(sum(r['outcome']=='EXECUTABLE_CONTRACT_PASS' for r in rows),suite_count)

    def test_only_explicit_empirical_events_can_become_relevance_feedback(self):
        from campaign_memory import CampaignEvent,to_feedback_events
        mech=CampaignEvent('m','c',0,'COMPOSITION','A->B','PASS','MECHANICS','s',supplier_id='A',consumer_id='B')
        empirical=CampaignEvent('e','c',1,'COMPOSITION','A->B','PASS','OOS','s',supplier_id='A',consumer_id='B',learning_eligible=True,release_generation=2)
        self.assertEqual(to_feedback_events((mech,)),())
        fb=to_feedback_events((empirical,))
        self.assertEqual(len(fb),1); self.assertEqual(fb[0].subject_id,'A'); self.assertEqual(fb[0].consumer_id,'B')

    def test_protected_validation_cannot_be_marked_learning_eligible(self):
        from campaign_memory import CampaignEvent
        with self.assertRaises(ValueError):
            CampaignEvent('p','c',1,'MECHANISM','A','PASS','PROTECTED_VALIDATION','s',learning_eligible=True,release_generation=2)

class AutoTelemetryRoutingTests(unittest.TestCase):
    def test_packet_auto_uses_canonical_telemetry_for_exact_bootstrap_shell(self):
        from experiment_contract_bootstrap import bootstrap_queue_row,_contract_to_dict
        from search_to_foundry import build_packet
        queue=json.loads((ROOT/'generated_v2_foundry'/'CORE_V2_FOUNDRY_COMPOSITION_QUEUE.json').read_text())
        row=next(r for r in queue if r['supplier_id']=='LCB-K009' and r['consumer_id']=='FOUNDRY:P026')
        draft=bootstrap_queue_row(row,root=ROOT,search_generation=2)
        problem={'problem_id':'AUTO_TELEM','objective':'constraint pressure capacity tipping','experiment_contract':_contract_to_dict(draft.contract)}
        packet=build_packet(problem,capability_k=3,primitive_k=3,expansion_seeds=2,suppliers_per_seed=2,incremental=False)
        gate=packet['experiment_selection']
        self.assertEqual(gate['status'],'ROUTED_FROM_FROZEN_AUTO_CALIBRATION')
        self.assertEqual(gate['calibration_source'],'CANONICAL_TELEMETRY_LEDGER')
        self.assertEqual(gate['plan']['selected_test_id'],draft.suite.test_id)

class SearchTraceTests(unittest.TestCase):
    def test_packet_carries_map_and_telemetry_fingerprints(self):
        from search_to_foundry import build_packet
        packet=build_packet({'problem_id':'R12_SMOKE','objective':'capacity constraint pressure tipping boundary','search_terms':['constraint pressure','capacity increase']},capability_k=5,primitive_k=4,expansion_seeds=3,suppliers_per_seed=3,incremental=False)
        self.assertEqual(packet['engine'],'LABALLCOMPASS_SEARCH_TO_FOUNDRY_R12')
        self.assertTrue(packet['research_trace']['interaction_map_fingerprint'])
        self.assertTrue(packet['research_trace']['telemetry_registry_fingerprint'])
        self.assertEqual(len(packet['packet_fingerprint']),64)

if __name__=='__main__': unittest.main()
