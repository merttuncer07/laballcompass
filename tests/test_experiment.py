import json,tempfile,unittest
from pathlib import Path
from maintenance.experiment import execute
class ExperimentTests(unittest.TestCase):
 def test_overwrite_confined_to_workspace(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t)/'source';d=root/'round';d.mkdir(parents=True);(d/'RESULT.json').write_text('frozen')
   (d/'run_experiment.py').write_text('from pathlib import Path\nPath(__file__).with_name("RESULT.json").write_text("new")\n')
   p=execute('round',root=root,runs=Path(t)/'runs');r=json.loads(p.read_text())
   self.assertEqual((d/'RESULT.json').read_text(),'frozen');self.assertEqual(r['status'],'EXECUTED');self.assertEqual(r['artifacts'][0]['path'],'round/RESULT.json')
 def test_error_has_receipt(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t)/'source';root.mkdir();(root/'run_experiment.py').write_text('raise RuntimeError("failed")')
   p=execute('.',root=root,runs=Path(t)/'runs');self.assertEqual(json.loads(p.read_text())['status'],'FAIL')
 def test_outside_entry_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t)
   with self.assertRaises(ValueError):execute('..',root=root,runs=root/'runs')
