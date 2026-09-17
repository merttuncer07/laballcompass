import unittest
from maintenance.components import resolve,target_matches
from maintenance.runner import discover
class ComponentTests(unittest.TestCase):
 def test_stable_foundry_id_routes_to_its_tests(self):
  r=resolve('P039');matched=[t for t in discover('all') if target_matches(r,t)];self.assertEqual(len(matched),1);self.assertIn('P039_CACF',matched[0].pattern)
 def test_recovered_id_routes_to_recovered_contract(self):
  r=resolve('V2P057');self.assertEqual(sum(target_matches(r,t) for t in discover('all')),1)
 def test_unknown_id_explained(self):
  with self.assertRaises(ValueError):resolve('NOT_REAL')


class ReadOnlyDiscoveryTests(unittest.TestCase):
 def test_show_uses_current_sources_without_rewriting_catalog(self):
  import contextlib, hashlib, io, json
  from unittest.mock import patch
  from maintenance.components import main
  from maintenance.runner import BASE, ROOT
  before=(BASE/'catalog.json').read_bytes()
  output=io.StringIO()
  with patch('maintenance.catalog.atomic',side_effect=AssertionError('Read-only discovery wrote a file')):
   with contextlib.redirect_stdout(output):
    self.assertEqual(main(['show','R014']),0)
  row=json.loads(output.getvalue())
  self.assertTrue(row['id'].startswith('R014_'))
  for source in row['python_sources']:
   self.assertEqual(source['sha256'],hashlib.sha256((ROOT/source['path']).read_bytes()).hexdigest())
  self.assertEqual((BASE/'catalog.json').read_bytes(),before)

 def test_explicit_build_still_persists_the_collected_catalog(self):
  from unittest.mock import patch
  from maintenance.catalog import build
  from maintenance.runner import BASE
  data={'schema_version':1,'components':[{'id':'unit_contract'}]}
  with patch('maintenance.catalog.collect',return_value=data), patch('maintenance.catalog.publish') as write:
   self.assertEqual(build(),1)
  write.assert_called_once_with(data)

class EfficientDiscoveryTests(unittest.TestCase):
 def test_exact_lookup_parses_only_selected_sources(self):
  import ast
  from unittest.mock import patch
  original=ast.parse
  with patch('maintenance.catalog.ast.parse',wraps=original) as parse:
   row=resolve('P083')
  self.assertEqual(parse.call_count,len(row['python_sources']))
  self.assertGreater(parse.call_count,0)

 def test_filtered_catalog_agrees_with_full_inventory(self):
  from maintenance.catalog import collect
  all_rows=collect()['components']
  for key in ('P083','R014','V2P057'):
   with self.subTest(key=key):
    expected=[r for r in all_rows if r['id']==key or r['id'].split('_')[0]==key]
    self.assertEqual(collect(component=key)['components'],expected)

 def test_pagination_bounds_output_and_labels_history(self):
  import contextlib,io
  from maintenance.components import main
  from unittest.mock import patch
  rows=[{'id':f'P{i}','layer':'foundry','latest_reproduction':{'status':'PASS'}} for i in range(30)]
  with patch('maintenance.components.catalog',return_value=rows), contextlib.redirect_stdout(io.StringIO()) as output:
   self.assertEqual(main(['components','--limit','2','--offset','3']),0)
  lines=output.getvalue().splitlines()
  self.assertEqual(len(lines),3)
  self.assertTrue(lines[0].startswith('P3 '))
  self.assertTrue(lines[1].startswith('P4 '))
  self.assertIn('historical',lines[2])

 def test_receipts_never_imply_current_source_verified(self):
  from maintenance.catalog import collect
  observed=[r['latest_reproduction'] for r in collect()['components'] if r['latest_reproduction']['receipt']]
  self.assertTrue(observed)
  self.assertTrue(all(r['current_source_verified'] is False for r in observed))


import json,tempfile
from pathlib import Path
from unittest.mock import patch
from maintenance import catalog as inventory
from maintenance.runner import BASE

class CatalogIndexTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.addCleanup(self.tmp.cleanup)
  self.index=self.root/'index.html';self.catalog_path=self.root/'catalog.json'
  self.rows=[{'id':'P039','layer':'foundry','status':'PASS'}]
  self.index.write_text('<!doctype html><title>t</title><script>const data=[];render();</script>',encoding='utf-8')
  mocked=patch.object(inventory,'BASE',self.root);mocked.start();self.addCleanup(mocked.stop)
 def publish(self):inventory.publish({'schema_version':1,'components':self.rows,'boundary':'x'})
 def load(self):return json.loads(self.catalog_path.read_text(encoding='utf-8'))
 def test_publish_updates_both_files(self):
  self.publish();self.assertEqual(self.load()['components'],self.rows)
  text=self.index.read_text(encoding='utf-8');marker='<script>const data='
  embedded,end=json.JSONDecoder().raw_decode(text[text.index(marker)+len(marker):])
  self.assertEqual(embedded,self.rows);self.assertTrue(text[text.index(marker)+len(marker)+end:].startswith(';render();</script>'))
 def test_malformed_index_preserves_existing_catalog(self):
  self.publish();old=self.catalog_path.read_bytes()
  self.index.write_text('<script>const data=[1,2;render();</script>',encoding='utf-8')
  with self.assertRaises(ValueError):self.publish()
  self.assertEqual(self.catalog_path.read_bytes(),old)
 def test_escaped_payload_roundtrips(self):
  self.rows=[{'id':'</script><b>x</b>&'}];self.publish()
  text=self.index.read_text(encoding='utf-8');self.assertNotIn('</script><b>',text);self.assertIn('\\u003c/script\\u003e',text)
  marker='<script>const data='
  embedded,_=json.JSONDecoder().raw_decode(text[text.index(marker)+len(marker):]);self.assertEqual(embedded,self.rows)
 def test_failed_index_replace_restores_catalog(self):
  self.publish();old=self.catalog_path.read_bytes();old_index=self.index.read_bytes();self.rows=[{'id':'changed'}]
  replace=inventory.os.replace
  def fail_index(source,destination):
   if Path(destination)==self.index:raise OSError('simulated index failure')
   return replace(source,destination)
  with patch.object(inventory.os,'replace',side_effect=fail_index):
   with self.assertRaises(OSError):self.publish()
  self.assertEqual(self.catalog_path.read_bytes(),old);self.assertEqual(self.index.read_bytes(),old_index)
 def test_real_index_marker_is_supported(self):
  text=(BASE/'index.html').read_text(encoding='utf-8')
  rendered=inventory.index_snapshot(text,self.rows)
  marker='<script>const data='
  embedded,_=json.JSONDecoder().raw_decode(rendered[rendered.index(marker)+len(marker):]);self.assertEqual(embedded,self.rows)
 def test_newer_failed_receipt_overrides_old_pass(self):
  root=self.root/'source';core=Path('core')
  for suffix in ['02_FOUNDRY_ALL_PRODUCTS/parent_products/CURRENT_PRODUCTS','02_FOUNDRY_ALL_PRODUCTS/parent_products/RETRO_PRODUCTS','02_FOUNDRY_ALL_PRODUCTS/products','01_V2_CORE/products']:
   (root/core/suffix).mkdir(parents=True,exist_ok=True)
  (root/'ACTIVE_RESEARCH'/'R001').mkdir(parents=True);(root/'ACTIVE_PRODUCTS').mkdir()
  for name,status in [('001','PASS'),('002','FAIL')]:
   folder=self.root/'runs'/name;folder.mkdir(parents=True)
   (folder/'receipt.json').write_text(json.dumps({'targets':[{'cwd':'ACTIVE_RESEARCH/R001','status':status}]}))
  with patch.object(inventory,'ROOT',root),patch.object(inventory,'CORE',core):self.assertEqual(inventory.build(),1)
  row=self.load()['components'][0]
  self.assertEqual(row['latest_reproduction']['status'],'FAIL');self.assertEqual(row['latest_reproduction']['receipt'],'runs/002/receipt.json')
