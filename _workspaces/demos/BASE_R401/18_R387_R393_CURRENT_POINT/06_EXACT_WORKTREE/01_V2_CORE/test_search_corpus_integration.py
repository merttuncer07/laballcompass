import json
import unittest
from pathlib import Path

from core_v2 import build_catalog_search_engine
from lab_search_engine import SearchQuery

ROOT=Path(__file__).resolve().parent

class SearchCorpusIntegrationTests(unittest.TestCase):
    def test_corpus_contains_capabilities_and_primitives(self):
        meta=json.loads((ROOT/'generated_search'/'LAB_SEARCH_CORPUS_COUNTS.json').read_text())
        self.assertEqual(meta['capabilities'],310)
        self.assertEqual(meta['primitives'],4000)
        self.assertEqual(meta['documents'],4310)

    def test_core_entrypoint_returns_exact_top_k(self):
        engine=build_catalog_search_engine()
        q=SearchQuery(text='memory lag selection holdout residual transport boundary gate',top_k=15)
        r=engine.full_search(q)
        self.assertEqual(tuple(h.document_id for h in r.hits),engine.naive_top_ids(q))
        self.assertEqual(len(r.hits),15)

if __name__=='__main__': unittest.main()

class SearchRelevanceSmokeTests(unittest.TestCase):
    def test_crypto_contract_recovers_declared_mechanism_anchors(self):
        from core_v2 import build_search_router
        obj=json.loads((ROOT/'generated_search'/'EXAMPLE_PROBLEM_CONTRACT_CRYPTO_V1.json').read_text())
        router=build_search_router()
        q=SearchQuery.from_dict(obj,top_k=20)
        ids=[h.document_id for h in router.search_capabilities(q,incremental=False).hits]
        for anchor in ('FOUNDRY:P137','LCB-K071','LCB-K089','LCB-K011','LCB-K069'):
            self.assertIn(anchor,ids)
