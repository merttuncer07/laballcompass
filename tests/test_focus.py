import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from maintenance.focus import MAX_BRIEF_BYTES, brief, load, main
from maintenance.runner import BASE


class FocusTests(unittest.TestCase):
    def setUp(self):
        self.data = load()

    def test_real_briefs_are_bounded_and_have_decision_criteria(self):
        for name in self.data["missions"]:
            result = brief(self.data, name)
            self.assertLessEqual(len(result.encode("utf-8")), MAX_BRIEF_BYTES)
            for label in ("Baseline:", "Success:", "Stop:", "Next action:", "Verification:"):
                self.assertIn(label, result)

    def test_default_is_the_single_active_mission(self):
        result = brief(self.data)
        self.assertIn(self.data["active"], result)
        self.assertIn("[active]", result)

    def test_unknown_mission_has_actionable_error(self):
        with self.assertRaisesRegex(ValueError, "focus --list"):
            brief(self.data, "unknown")

    def test_oversized_brief_rejected_without_silent_truncation(self):
        self.data["missions"][self.data["active"]]["goal"] = "x" * MAX_BRIEF_BYTES
        with self.assertRaisesRegex(ValueError, "exceeds"):
            brief(self.data)

    def load_modified(self, mutate):
        data = copy.deepcopy(self.data)
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            (base / "evidence.md").write_text("test")
            for mission in data["missions"].values():
                mission["read"] = mission["evidence"] = ["evidence.md"]
            mutate(data)
            (base / "lab-focus.json").write_text(json.dumps(data))
            return load(base)

    def test_absent_baseline_rejected(self):
        with self.assertRaisesRegex(ValueError, "missing baseline"):
            self.load_modified(lambda d: d["missions"][d["active"]].pop("baseline"))

    def test_multiple_active_missions_rejected(self):
        with self.assertRaisesRegex(ValueError, "Exactly one"):
            self.load_modified(lambda d: d["missions"]["information-selection"].update(status="active"))

    def test_missing_evidence_rejected(self):
        with self.assertRaisesRegex(ValueError, "missing or unsafe"):
            self.load_modified(lambda d: d["missions"][d["active"]].update(evidence=["missing.md"]))

    def test_outside_or_absolute_evidence_rejected(self):
        for path in ("../outside.md", str(BASE / "lab.py")):
            with self.subTest(path=path), self.assertRaisesRegex(ValueError, "missing or unsafe"):
                self.load_modified(lambda d: d["missions"][d["active"]].update(evidence=[path]))

    def test_focus_does_not_collect_catalog_or_run_tests(self):
        import contextlib
        import io
        with patch("maintenance.catalog.collect", side_effect=AssertionError("catalog scan")), \
                patch("maintenance.runner.run", side_effect=AssertionError("test run")), \
                contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main([]), 0)
        self.assertIn("Focus:", output.getvalue())


if __name__ == "__main__":
    unittest.main()
