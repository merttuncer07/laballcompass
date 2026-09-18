import json,tempfile,unittest
from pathlib import Path
from maintenance.runner import Target,run,counts,discover,doctor,parent_test_runner

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
  hashes=json.loads((p.parent/'source-hashes.json').read_text())
  self.assertIn('../lab.py',hashes)
  self.assertIn('../workbench/report.py',hashes)
  self.assertIn('Python source only',r['source_snapshot_scope'])
 def test_all_includes_application_and_no_duplicate_restoration_target(self):
  targets=discover('all')
  app=[t for t in targets if t.id=='LAB_APPLICATION']
  self.assertEqual(len(app),1)
  self.assertEqual((app[0].cwd,app[0].runner,app[0].pattern),('..','pytest','tests'))
  self.assertNotIn('RESTORATION_REGRESSIONS',[t.id for t in targets])
  self.assertEqual(discover('lab'),app)
  self.assertEqual(len(discover('repairs')),1)
 def test_quiet_preserves_logs_and_prints_failures(self):
  import contextlib,io
  ok=self.target('quietok','import unittest\nclass Test(unittest.TestCase):\n def test_ok(self):pass\n')
  bad=self.target('quietbad','import unittest\nclass Test(unittest.TestCase):\n def test_bad(self):self.fail("kept failure")\n')
  with contextlib.redirect_stdout(io.StringIO()) as output:
   p,r=self.execute([ok,bad],quiet=True)
  text=output.getvalue()
  self.assertNotIn('quietok: PASS',text)
  self.assertIn('quietbad: FAIL',text)
  self.assertIn('FAIL: 1/2 tests passed',text)
  self.assertIn('kept failure',(p.parent/r['targets'][1]['log']).read_text())
 def test_discovery_matches_current_scope(self):
  active=discover('active');self.assertEqual(len(active),24);self.assertEqual(len(discover('full')),92)
  self.assertIn('R211_VOLTERRA_ACTIVE_PROBE_TRANSFER',[target.id for target in active])
  self.assertIn('R212_VOLTERRA_NO_RESET_INTRINSIC',[target.id for target in active])
 def test_real_parent_function_regressions_are_collected(self):
  targets={t.id:t for t in discover('parents')}
  self.assertEqual(targets['R014_S781_S792_ACSA'].runner,'pytest')
  self.assertEqual(targets['R027_S426_S427_MIFF'].runner,'pytest')
  self.assertEqual(targets['R026_S423_S424_EBC'].runner,'unittest')
 def test_function_failure_cannot_hide_behind_passing_unittest_suite(self):
  target=self.target('mixed','import unittest\nclass Test(unittest.TestCase):\n def test_ok(self):pass\ndef test_regression():\n assert False, "regression must be collected"\n')
  target.runner=parent_test_runner(self.root/target.cwd)
  _,receipt=self.execute([target])
  self.assertEqual(receipt['status'],'FAIL')
  self.assertEqual(receipt['counts']['tests'],2)
  self.assertEqual(receipt['counts']['failures'],1)
 def test_bad_test_module_does_not_abort_component_discovery(self):
  bad=self.target('badsyntax','def test_broken(:\n pass\n')
  bad.runner=parent_test_runner(self.root/bad.cwd)
  after=self.target('afterbad','import unittest\nclass Test(unittest.TestCase):\n def test_ok(self):pass\n')
  _,receipt=self.execute([bad,after])
  self.assertEqual([t['status'] for t in receipt['targets']],['FAIL','PASS'])
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
