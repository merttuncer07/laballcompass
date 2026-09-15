import random
import unittest
from dataclasses import replace

from lab_search_engine import CertifiedIncrementalSearch, SearchDocument, SearchQuery


def docs():
    return [
        SearchDocument('a','Memory Guard','CAP','memory lag holdout selection guard',frozenset({'selection'}),frozenset({'evidence'}),frozenset({'gate'}),evidence_tier='MECHANISM_BENCHMARKED',component_value=3),
        SearchDocument('b','Variance Alarm','CAP','predictable variance drift alarm',frozenset({'uncertainty'}),frozenset({'metric'}),frozenset({'gate'}),evidence_tier='EXECUTABLE',component_value=2),
        SearchDocument('c','Allocator','CAP','capacity allocation budget optimizer',frozenset({'allocation'}),frozenset({'evidence'}),frozenset({'allocation'}),evidence_tier='EXECUTABLE',component_value=2),
        SearchDocument('d','Transport Gate','CAP','transport residual invariance gate',frozenset({'audit'}),frozenset({'representation'}),frozenset({'gate'}),evidence_tier='EXECUTABLE',component_value=2),
        SearchDocument('e','Graph Primitive','PRIMITIVE','graph cycle flow network',domains=frozenset({'mathematics'})),
        SearchDocument('f','Memory Primitive','PRIMITIVE','long memory kernel closure lag persistence',domains=frozenset({'physics'})),
    ]


class CertifiedSearchTests(unittest.TestCase):
    def test_full_matches_naive(self):
        e=CertifiedIncrementalSearch(docs())
        q=SearchQuery(text='memory lag selection',top_k=3)
        r=e.full_search(q)
        self.assertEqual(tuple(h.document_id for h in r.hits),e.naive_top_ids(q))

    def test_unrelated_feature_reuses_everything(self):
        e=CertifiedIncrementalSearch(docs())
        q=SearchQuery(text='memory lag',top_k=2)
        e.full_search(q)
        r=e.update(replace(q,text='memory lag extraterrestrialfoobar'))
        self.assertEqual(r.status,'QUERY_DELTA_NO_DOCUMENT_DEPENDENCY_REUSE')
        self.assertEqual(r.exact_rescored_this_update,0)
        self.assertEqual(tuple(h.document_id for h in r.hits),e.naive_top_ids(replace(q,text='memory lag extraterrestrialfoobar')))

    def test_relevant_small_change_is_certified_or_selective_and_exact(self):
        e=CertifiedIncrementalSearch(docs())
        q=SearchQuery(text='memory lag selection',top_k=2)
        e.full_search(q)
        q2=replace(q,text='memory lag selection persistence')
        r=e.update(q2)
        self.assertLess(r.exact_rescored_this_update,len(docs()))
        self.assertEqual(tuple(h.document_id for h in r.hits),e.naive_top_ids(q2))

    def test_strong_query_shift_changes_frontier_correctly(self):
        e=CertifiedIncrementalSearch(docs())
        q=SearchQuery(text='memory lag',top_k=2)
        e.full_search(q)
        q2=SearchQuery(text='capacity allocation optimizer',preferred_output_types=('allocation',),top_k=2)
        r=e.update(q2)
        self.assertEqual(tuple(h.document_id for h in r.hits),e.naive_top_ids(q2))
        self.assertIn('c',tuple(h.document_id for h in r.hits))

    def test_cumulative_updates_never_diverge(self):
        e=CertifiedIncrementalSearch(docs())
        q=SearchQuery(text='memory',top_k=3)
        e.full_search(q)
        words=['lag','selection','variance','drift','transport','graph','capacity','persistence','unknownword']
        active=['memory']
        for i in range(80):
            w=words[i%len(words)]
            if w in active: active.remove(w)
            else: active.append(w)
            q=SearchQuery(text=' '.join(active),top_k=3)
            r=e.update(q)
            self.assertEqual(tuple(h.document_id for h in r.hits),e.naive_top_ids(q))

    def test_random_differential_against_naive(self):
        rng=random.Random(17)
        e=CertifiedIncrementalSearch(docs())
        vocab=['memory','lag','selection','variance','drift','transport','graph','capacity','persistence','allocation','foobar']
        active=set(['memory','lag'])
        q=SearchQuery(text=' '.join(sorted(active)),top_k=3)
        e.full_search(q)
        for _ in range(250):
            w=rng.choice(vocab)
            if w in active: active.remove(w)
            else: active.add(w)
            q=SearchQuery(text=' '.join(sorted(active)),top_k=3)
            r=e.update(q)
            self.assertEqual(tuple(h.document_id for h in r.hits),e.naive_top_ids(q))

    def test_top_k_change_fails_closed_to_full_search(self):
        e=CertifiedIncrementalSearch(docs())
        e.full_search(SearchQuery(text='memory',top_k=2))
        r=e.update(SearchQuery(text='memory',top_k=3))
        self.assertEqual(r.status,'FULL_SEARCH')
        self.assertEqual(r.exact_rescored_this_update,len(docs()))

if __name__=='__main__': unittest.main()

class InteractionSearchTests(unittest.TestCase):
    def test_identity_seed_propagates_to_connected_supplier(self):
        from lab_search_engine import InteractionGraph
        d=[
            SearchDocument('consumer','Target','CAP','target only',metadata={'kind':'capability'}),
            SearchDocument('supplier','Repair','CAP','unrelated words',metadata={'kind':'capability'}),
            SearchDocument('other','Other','CAP','unrelated words',metadata={'kind':'capability'}),
        ]
        g=InteractionGraph({'consumer':{'supplier':0.5}})
        e=CertifiedIncrementalSearch(d,interaction_graph=g,excluded_ids={'consumer'})
        q=SearchQuery(seed_document_ids=('consumer',),top_k=1)
        r=e.full_search(q)
        self.assertEqual(r.hits[0].document_id,'supplier')
        self.assertEqual(tuple(h.document_id for h in r.hits),e.naive_top_ids(q))

    def test_interaction_incremental_update_matches_full_search(self):
        from lab_search_engine import InteractionGraph
        d=[
            SearchDocument('consumer','Target','CAP','target selection',metadata={'kind':'capability'}),
            SearchDocument('supplier','Repair','CAP','drift alarm',metadata={'kind':'capability'}),
            SearchDocument('other','Other','CAP','variance alarm',metadata={'kind':'capability'}),
        ]
        g=InteractionGraph({'consumer':{'supplier':0.45}})
        e=CertifiedIncrementalSearch(d,interaction_graph=g,excluded_ids={'consumer'})
        q=SearchQuery(text='drift',seed_document_ids=('consumer',),top_k=2)
        e.full_search(q)
        q2=SearchQuery(text='drift variance',seed_document_ids=('consumer',),top_k=2)
        r=e.update(q2)
        self.assertEqual(tuple(h.document_id for h in r.hits),e.naive_top_ids(q2))

class SearchSnapshotTests(unittest.TestCase):
    def test_snapshot_restore_preserves_incremental_equivalence(self):
        e=CertifiedIncrementalSearch(docs())
        q=SearchQuery(text='memory lag selection',top_k=3)
        e.full_search(q)
        snap=e.snapshot()
        clone=CertifiedIncrementalSearch(docs())
        self.assertTrue(clone.restore_snapshot(snap))
        q2=SearchQuery(text='memory lag selection persistence',top_k=3)
        r=clone.update(q2)
        self.assertEqual(tuple(h.document_id for h in r.hits),clone.naive_top_ids(q2))

    def test_snapshot_fails_closed_on_corpus_change(self):
        e=CertifiedIncrementalSearch(docs())
        e.full_search(SearchQuery(text='memory',top_k=2))
        altered=docs()+[SearchDocument('g','New','CAP','memory extra')]
        clone=CertifiedIncrementalSearch(altered)
        self.assertFalse(clone.restore_snapshot(e.snapshot()))
        r=clone.update(SearchQuery(text='memory',top_k=2))
        self.assertEqual(r.status,'FULL_SEARCH')
