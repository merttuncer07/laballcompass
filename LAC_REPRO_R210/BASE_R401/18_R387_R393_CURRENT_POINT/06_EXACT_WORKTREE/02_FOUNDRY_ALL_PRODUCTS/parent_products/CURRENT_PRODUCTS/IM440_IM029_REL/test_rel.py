from __future__ import annotations

import unittest

from rel import ConsistencyRelation, EvidenceRecord, RelationalEvidenceLocalizer


class RelationalEvidenceLocalizerTests(unittest.TestCase):
    def test_single_altered_record_is_localized(self) -> None:
        records = [
            EvidenceRecord("a", "one", 10),
            EvidenceRecord("b", "two", 20),
            EvidenceRecord("c", "three", 10),
        ]
        relations = [
            ConsistencyRelation("ab", "a", "b"),
            ConsistencyRelation("bc", "b", "c"),
            ConsistencyRelation("ac", "a", "c"),
        ]
        result = RelationalEvidenceLocalizer().localize(records, relations, 1)
        self.assertEqual(result["top_candidate"]["records"], ("b",))

    def test_coherent_pair_can_be_localized(self) -> None:
        records = [
            EvidenceRecord("a", "one", 10, 0.01),
            EvidenceRecord("b", "two", 20, 0.10),
            EvidenceRecord("c", "three", 20, 0.10),
            EvidenceRecord("d", "four", 10, 0.01),
        ]
        relations = [
            ConsistencyRelation("ab", "a", "b"),
            ConsistencyRelation("ac", "a", "c"),
            ConsistencyRelation("bd", "b", "d"),
            ConsistencyRelation("cd", "c", "d"),
            ConsistencyRelation("bc", "b", "c"),
            ConsistencyRelation("ad", "a", "d"),
        ]
        result = RelationalEvidenceLocalizer().localize(records, relations, 2)
        self.assertEqual(set(result["top_candidate"]["records"]), {"b", "c"})

    def test_missing_record_reference_is_rejected(self) -> None:
        with self.assertRaises(KeyError):
            RelationalEvidenceLocalizer().localize(
                [EvidenceRecord("a", "one", 1)],
                [ConsistencyRelation("missing", "a", "b")],
            )

    def test_consistent_records_do_not_force_a_suspect(self):
        records = [EvidenceRecord(n, n, 10) for n in ('a', 'b', 'c')]
        result = RelationalEvidenceLocalizer().localize(records, [ConsistencyRelation('ab', 'a', 'b')])
        self.assertEqual(result['top_candidate']['records'], ())
        self.assertGreater(result['top_candidate']['posterior'], 0.9)

    def test_repeating_or_reversing_a_comparison_adds_no_weight(self):
        records = [EvidenceRecord('a', 'a', 10), EvidenceRecord('b', 'b', 20)]
        engine = RelationalEvidenceLocalizer()
        once = engine.localize(records, [ConsistencyRelation('ab', 'a', 'b')])
        repeated = engine.localize(records, [ConsistencyRelation(str(i), *('ab' if i % 2 else 'ba')) for i in range(100)])
        weights = lambda r: {x['records']: x['posterior'] for x in r['ranking']}
        self.assertEqual(weights(once), weights(repeated))
        self.assertEqual(repeated['unique_observation_count'], 1)
        self.assertEqual(len(repeated['observed_violations']), 100)

    def test_different_thresholds_on_same_pair_are_not_independent_tests(self):
        with self.assertRaisesRegex(ValueError, 'joint observation'):
            RelationalEvidenceLocalizer().localize(
                [EvidenceRecord('a', 'a', 10), EvidenceRecord('b', 'b', 20)],
                [ConsistencyRelation('one', 'a', 'b', 0), ConsistencyRelation('two', 'b', 'a', 15)])

    def test_no_observations_retains_null_and_normalized_model_prior(self):
        result = RelationalEvidenceLocalizer().localize([EvidenceRecord('a', 'a', 10)], [])
        self.assertEqual(result['top_candidate']['records'], ())
        self.assertAlmostEqual(sum(x['posterior'] for x in result['ranking']), 1)
        self.assertEqual(result['unique_observation_count'], 0)

    def test_uninformative_sensor_does_not_change_prior_weights(self):
        records = [EvidenceRecord('a', 'a', 10), EvidenceRecord('b', 'b', 20)]
        engine = RelationalEvidenceLocalizer(detection_probability=.3, false_violation_probability=.3)
        prior = engine.localize(records, [])
        observed = engine.localize(records, [ConsistencyRelation('ab', 'a', 'b')])
        for a, b in zip(prior['ranking'], observed['ranking']):
            self.assertEqual(a['records'], b['records'])
            self.assertAlmostEqual(a['posterior'], b['posterior'])


if __name__ == "__main__":
    unittest.main()
