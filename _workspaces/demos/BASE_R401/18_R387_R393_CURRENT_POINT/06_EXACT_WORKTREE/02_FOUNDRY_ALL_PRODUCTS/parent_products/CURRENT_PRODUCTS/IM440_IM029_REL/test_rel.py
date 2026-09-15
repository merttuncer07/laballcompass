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


if __name__ == "__main__":
    unittest.main()
