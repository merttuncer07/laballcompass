import unittest

from lab_search_engine import CertifiedIncrementalSearch, LabSearchRouter, SearchDocument, SearchQuery
from relevance_learning import (
    FeedbackEvent, FeedbackLedger, compile_relevance_snapshot,
    LEARN_AFTER_GENERATION, PROTECTED_VALIDATION, DIAGNOSTIC_ONLY,
    HELPED, HURT,
)


def docs():
    return [
        SearchDocument('a','Alpha','F1','memory repair',metadata={'kind':'capability'}),
        SearchDocument('b','Beta','F1','memory repair',metadata={'kind':'capability'}),
        SearchDocument('c','Gamma','F2','memory repair',metadata={'kind':'capability'}),
        SearchDocument('consumer','Consumer','TARGET','target state',weakness_tags=frozenset({'repair'}),input_types=frozenset({'gate'}),metadata={'kind':'capability'}),
        SearchDocument('supplier_a','Supplier A','SUP','unrelated',strength_tags=frozenset({'repair'}),output_types=frozenset({'gate'}),metadata={'kind':'capability'}),
        SearchDocument('supplier_b','Supplier B','SUP','unrelated',strength_tags=frozenset({'repair'}),output_types=frozenset({'gate'}),metadata={'kind':'capability'}),
        SearchDocument('prim','Primitive','PRIMITIVE','primitive mechanism',metadata={'kind':'primitive'}),
    ]


class RelevanceLearningTests(unittest.TestCase):
    def test_same_generation_feedback_is_quarantined(self):
        ledger=FeedbackLedger([
            FeedbackEvent('e1','a',selection_generation=2,release_generation=2,problem_shell='crypto',outcome=HELPED),
        ])
        snap=compile_relevance_snapshot(ledger,docs(),target_generation=2,problem_shell='crypto')
        self.assertEqual(dict(snap.document_offsets),{})
        self.assertEqual(snap.included_event_ids,())
        self.assertEqual(snap.quarantined_events[0]['reason'],'SAME_OR_FUTURE_GENERATION_QUARANTINE')

    def test_closed_prior_generation_can_train_next_generation(self):
        ledger=FeedbackLedger([
            FeedbackEvent('e1','a',selection_generation=1,release_generation=1,problem_shell='crypto',outcome=HELPED),
            FeedbackEvent('e2','b',selection_generation=1,release_generation=1,problem_shell='crypto',outcome=HURT),
        ])
        snap=compile_relevance_snapshot(ledger,docs(),target_generation=2,problem_shell='crypto')
        self.assertGreater(snap.document_offsets['a'],0)
        self.assertLess(snap.document_offsets['b'],0)
        self.assertEqual(set(snap.included_event_ids),{'e1','e2'})

    def test_protected_validation_never_trains_even_later(self):
        ledger=FeedbackLedger([
            FeedbackEvent('e1','a',selection_generation=0,release_generation=0,problem_shell='crypto',outcome=HELPED,role=PROTECTED_VALIDATION),
        ])
        snap=compile_relevance_snapshot(ledger,docs(),target_generation=99,problem_shell='crypto')
        self.assertNotIn('a',snap.document_offsets)
        self.assertEqual(snap.quarantined_events[0]['reason'],'PROTECTED_VALIDATION_NEVER_TRAINS')

    def test_out_of_scope_shell_does_not_transfer_without_shared_tags(self):
        ledger=FeedbackLedger([
            FeedbackEvent('e1','a',0,0,'medical',HELPED,shell_tags=('clinical',)),
        ])
        snap=compile_relevance_snapshot(ledger,docs(),target_generation=1,problem_shell='crypto',shell_tags=('trading',))
        self.assertEqual(dict(snap.document_offsets),{})
        self.assertEqual(snap.quarantined_events[0]['reason'],'OUT_OF_SCOPE_SHELL')

    def test_pair_feedback_is_consumer_specific(self):
        ledger=FeedbackLedger([
            FeedbackEvent('p1','supplier_a',0,0,'shell',HELPED,consumer_id='consumer'),
        ])
        snap=compile_relevance_snapshot(ledger,docs(),target_generation=1,problem_shell='shell')
        self.assertNotIn('supplier_a',snap.document_offsets)
        self.assertGreater(snap.supplier_offsets_by_consumer['consumer']['supplier_a'],0)
        self.assertNotIn('other_consumer',snap.supplier_offsets_by_consumer)

    def test_router_uses_pair_prior_only_for_supplier_surface(self):
        ledger=FeedbackLedger([
            FeedbackEvent('p1','supplier_a',0,0,'shell',HELPED,consumer_id='consumer'),
            FeedbackEvent('p2','supplier_b',0,0,'shell',HURT,consumer_id='consumer'),
        ])
        snap=compile_relevance_snapshot(ledger,docs(),target_generation=1,problem_shell='shell')
        router=LabSearchRouter(docs(),relevance_snapshot=snap)
        result=router.search_suppliers('consumer','',top_k=2,incremental=False)
        self.assertEqual(result.hits[0].document_id,'supplier_a')
        # Pair-specific feedback did not become a global direct-search bonus.
        q=SearchQuery(text='unrelated',top_k=6)
        direct=router.search_capabilities(q,incremental=False)
        expl=router.capability_engine.explain_score('supplier_a',q)
        self.assertEqual(expl['learned_relevance_prior'],0.0)

    def test_feedback_snapshot_change_invalidates_incremental_cache(self):
        base=CertifiedIncrementalSearch(docs())
        base.full_search(SearchQuery(text='memory repair',top_k=2))
        state=base.snapshot()
        learned=CertifiedIncrementalSearch(docs(),score_offsets={'a':0.25})
        self.assertFalse(learned.restore_snapshot(state))
        result=learned.update(SearchQuery(text='memory repair',top_k=2))
        self.assertEqual(result.status,'FULL_SEARCH')

    def test_frozen_snapshot_is_immutable_to_later_ledger_append(self):
        ledger=FeedbackLedger([FeedbackEvent('old','a',0,0,'shell',HELPED)])
        frozen=compile_relevance_snapshot(ledger,docs(),target_generation=1,problem_shell='shell')
        before=dict(frozen.document_offsets)
        ledger.append(FeedbackEvent('new','c',1,1,'shell',HELPED))
        self.assertEqual(dict(frozen.document_offsets),before)
        self.assertNotIn('c',frozen.document_offsets)


if __name__=='__main__': unittest.main()
