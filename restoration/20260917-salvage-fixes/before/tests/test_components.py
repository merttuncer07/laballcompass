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
  with patch('maintenance.catalog.collect',return_value=data), patch('maintenance.catalog.atomic') as write:
   self.assertEqual(build(),1)
  write.assert_called_once_with(BASE/'catalog.json',data)

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
