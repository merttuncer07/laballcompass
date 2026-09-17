import csv,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
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
 def test_spec_changes_after_parsing_keep_original_provenance(self):
  expected=self.call();original_loads=json.loads
  def load_and_change(*args,**kwargs):
   spec=original_loads(*args,**kwargs)
   self.spec.write_text('{}')
   return spec
  with patch('maintenance.compare.json.loads',side_effect=load_and_change):
   result=evaluate(self.spec,self.data)
  self.assertEqual(self.spec.read_text(),'{}')
  self.assertEqual(result,expected)
 def test_data_changes_after_parsing_keep_original_provenance(self):
  expected=self.call();original_reader=csv.DictReader
  def read_and_change(*args,**kwargs):
   yield from original_reader(*args,**kwargs)
   self.data.write_text('changed after parsing\n')
  with patch('maintenance.compare.csv.DictReader',side_effect=read_and_change):
   result=evaluate(self.spec,self.data)
  self.assertEqual(self.data.read_text(),'changed after parsing\n')
  self.assertEqual(result,expected)
 def test_each_input_is_read_once(self):
  expected=self.call();reads={self.spec:0,self.data:0};original_open=Path.open
  def count_open(path,*args,**kwargs):
   if path in reads:reads[path]+=1
   return original_open(path,*args,**kwargs)
  with patch.object(Path,'open',count_open):
   result=evaluate(self.spec,self.data)
  self.assertEqual(result,expected)
  self.assertEqual(reads,{self.spec:1,self.data:1})
if __name__=='__main__':unittest.main()
