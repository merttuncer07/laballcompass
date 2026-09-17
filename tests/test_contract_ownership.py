"""In-memory ownership counterexamples; these are not field/audit evidence."""
import json
import unittest
from workbench.contracts import DependencyProblem
from workbench.methods import METHODS


class ContractOwnershipTests(unittest.TestCase):
    def make_problem(self):
        bases = {'a': 'A', 'b': 'B'}
        body = ['a', 'b']
        rules = [['t', body]]
        targets = ['t']
        metadata = {'labels': {'a': 'original'}, 'observations': [{'rows': [1, 2]}]}
        problem = DependencyProblem('ownership', bases, rules, targets, metadata=metadata)
        return problem, bases, body, rules, targets, metadata

    def test_constructor_owns_semantics_and_nested_metadata(self):
        p, bases, body, rules, targets, metadata = self.make_problem()
        original = json.loads(json.dumps(p.to_dict()))
        digest = p.digest()
        bases['a'] = ''
        body.append('missing')
        rules.clear()
        targets.clear()
        metadata['observations'][0]['rows'].append(3)
        self.assertEqual(p.to_dict(), original)
        self.assertEqual(p.digest(), digest)
        self.assertEqual(p.sources, ('A', 'B'))
        self.assertEqual(p.rules, (('t', ('a', 'b')),))
        self.assertEqual(p.targets, ('t',))

    def test_export_can_be_edited_without_changing_compiled_or_live_analysis(self):
        p, *_ = self.make_problem()
        models = [method(p) for method in METHODS.values()]
        original = json.loads(json.dumps(p.to_dict()))
        digest = p.digest()
        exported = p.to_dict()
        exported['bases']['a'] = 'unvalidated-source'
        exported['rules'][0]['body'].clear()
        exported['targets'].clear()
        exported['metadata']['observations'][0]['rows'].append(3)
        self.assertEqual(p.to_dict(), original)
        self.assertEqual(p.digest(), digest)
        for model in models:
            with self.subTest(method=model.id):
                self.assertEqual(model.solve([set(), {'A'}]), [{'t': True}, {'t': False}])

    def test_semantic_mapping_cannot_bypass_validation(self):
        p, *_ = self.make_problem()
        with self.assertRaises(TypeError):
            p.bases['a'] = ''

    def test_json_roundtrip_preserves_schema_and_detaches_nested_annotations(self):
        p, *_ = self.make_problem()
        document = json.loads(json.dumps(p.to_dict()))
        loaded = DependencyProblem.from_dict(document)
        self.assertEqual(loaded.to_dict(), document)
        self.assertEqual(loaded.digest(), p.digest())
        document['metadata']['labels']['a'] = 'changed'
        self.assertEqual(loaded.metadata['labels']['a'], 'original')


if __name__ == '__main__':
    unittest.main()
