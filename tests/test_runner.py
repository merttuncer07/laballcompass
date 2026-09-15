import json,tempfile,unittest
from pathlib import Path
from maintenance.runner import Target,run,counts,discover,doctor

class RunnerTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)/'source';self.root.mkdir();self.runs=Path(self.temp.name)/'runs'
 def tearDown(self):self.temp.cleanup()
 def target(self,name,code):
  d=self.root/name;d.mkdir();(d/'test_case.py').write_text(code);return Target(name,name,'unittest')
 def execute(self,targets,**kw):
  p=run(targets,root=self.root,runs=self.runs,verify=False,**kw);return p,json.loads(p.read_text())
 def test_failure_retains_pass_and_continues(self):
  a=self.target('pass','import unittest\nclass Test(unittest.TestCase):\n def test_ok(self):self.assertTrue(True)\n')
  b=self.target('fail','import unittest\nclass Test(unittest.TestCase):\n def test_fail(self):self.fail("intentional")\n')
  c=self.target('after','import unittest\nclass Test(unittest.TestCase):\n def test_ok(self):self.assertTrue(True)\n')
  p,r=self.execute([a,b,c]);self.assertEqual([x['status'] for x in r['targets']],['PASS','FAIL','PASS']);self.assertEqual(r['counts']['passed'],2);self.assertEqual(r['status'],'FAIL')
 def test_empty_suite_not_pass(self):
  _,r=self.execute([self.target('empty','x=1\n')]);self.assertEqual(r['status'],'FAIL')
 def test_skipped_is_not_passed(self):
  t=self.target('skip','import unittest\nclass Test(unittest.TestCase):\n @unittest.skip("reason")\n def test_skip(self):pass\n')
  _,r=self.execute([t]);self.assertEqual(r['counts']['skipped'],1);self.assertEqual(r['counts']['passed'],0);self.assertEqual(r['status'],'FAIL')
 def test_timeout_recorded(self):
  t=self.target('timeout','import time\ntime.sleep(30)\n');_,r=self.execute([t],timeout=.15);self.assertEqual(r['targets'][0]['status'],'TIMEOUT');self.assertEqual(r['status'],'FAIL')
 def test_runs_do_not_overwrite(self):
  t=self.target('ok','import unittest\nclass Test(unittest.TestCase):\n def test_ok(self):pass\n')
  a,ra=self.execute([t]);b,rb=self.execute([t]);self.assertNotEqual(a,b);self.assertEqual(json.loads(a.read_text()),ra);self.assertEqual(rb['status'],'PASS')
 def test_junit_counts_actual_cases(self):
  p=self.root/'report.xml';p.write_text('<testsuites><testsuite><testcase/><testcase><skipped/></testcase><testcase><failure/></testcase></testsuite></testsuites>')
  c=counts(p,'pytest');self.assertEqual((c['tests'],c['passed'],c['skipped'],c['failures']),(3,1,1,1))
 def test_no_targets_is_error(self):
  with self.assertRaises(ValueError):self.execute([])
 def test_source_and_environment_receipts(self):
  t=self.target('ok','import unittest\nclass Test(unittest.TestCase):\n def test_ok(self):pass\n');p,r=self.execute([t]);self.assertTrue((p.parent/'source-hashes.json').exists());self.assertIn('packages',r['environment']);self.assertEqual(r['results_scope'],'software_reproduction_only')
 def test_discovery_matches_original_scope(self):
  self.assertEqual(len(discover('active')),22);self.assertEqual(len(discover('full')),90)
 def test_editing_source_does_not_block_normal_tests(self):
  t=self.target('edited','import unittest\nclass Test(unittest.TestCase):\n def test_ok(self):pass\n')
  (self.root/'verify_package.py').write_text('raise SystemExit(1)\n')
  p=run([t],root=self.root,runs=self.runs)
  r=json.loads(p.read_text());self.assertEqual(r['status'],'PASS');self.assertEqual(r['integrity']['status'],'NOT_REQUESTED')
 def test_explicit_package_verification_still_blocks_mismatch(self):
  t=self.target('edited','import unittest\nclass Test(unittest.TestCase):\n def test_ok(self):pass\n')
  (self.root/'verify_package.py').write_text('raise SystemExit(1)\n')
  p=run([t],root=self.root,runs=self.runs,verify=True)
  r=json.loads(p.read_text());self.assertEqual(r['status'],'FAIL');self.assertEqual(r['targets'][0]['status'],'PENDING');self.assertEqual(r['integrity']['exit_code'],1)
if __name__=='__main__':unittest.main()
