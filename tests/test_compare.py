import csv,json,tempfile,unittest
from pathlib import Path
from maintenance.compare import evaluate
class ComparisonTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.spec=self.root/'spec.json';self.data=self.root/'data.csv'
  self.design={'candidate':'new','baseline':'base','metric':'loss','unit':'squared_error','direction':'minimize','cases':['easy','hard'],'replicates':['a','b','c','d','e'],'replication_kind':'independent_blocks'}
  self.rows=[{'method':m,'case':c,'replicate':r,'value':v} for c in self.design['cases'] for r in self.design['replicates'] for m,v in [('new',2 if c=='easy' else 6),('base',4)]]
 def tearDown(self):self.tmp.cleanup()
 def call(self):
  self.spec.write_text(json.dumps(self.design))
  with self.data.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=['method','case','replicate','value']);w.writeheader();w.writerows(self.rows)
  return evaluate(self.spec,self.data)
 def test_average_does_not_hide_worse_case(self):
  r=self.call();self.assertEqual(r['mean_gain'],0);self.assertEqual(r['worsened_cases'],['hard']);self.assertEqual(r['promotion'],'NOT_ASSESSED');self.assertEqual(r['interval']['low'],0)
 def test_missing_baseline_rejected(self):
  self.rows.pop()
  with self.assertRaises(ValueError):self.call()
 def test_duplicate_not_independent(self):
  self.rows.append(self.rows[0])
  with self.assertRaises(ValueError):self.call()
 def test_nonfinite_rejected(self):
  self.rows[0]['value']='NaN'
  with self.assertRaises(ValueError):self.call()
 def test_timing_repetitions_not_independent(self):
  self.design['replication_kind']='timing_repeats';self.assertIsNone(self.call()['interval'])
 def test_deterministic_bootstrap(self):self.assertEqual(self.call()['interval'],self.call()['interval'])
if __name__=='__main__':unittest.main()
