#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
from maintenance import runner
from maintenance.compare import evaluate
if len(sys.argv)>1 and sys.argv[1]=='workbench':
 from workbench.cli import main
 sys.exit(main(sys.argv[2:]))
elif len(sys.argv)>1 and sys.argv[1]=='flow-review':
 import runpy
 source=runner.ROOT/runner.CORE/'02_FOUNDRY_ALL_PRODUCTS/products/P103_CFAI/cfai.py'
 sys.argv=[str(source),*sys.argv[2:]]
 runpy.run_path(str(source),run_name='__main__')
elif len(sys.argv)>1 and sys.argv[1]=='select-information':
 import runpy
 source=runner.ROOT/runner.CORE/'02_FOUNDRY_ALL_PRODUCTS/parent_products/CURRENT_PRODUCTS/IM359_IM014_AICC/aicc.py'
 sys.argv=[str(source),*sys.argv[2:]]
 runpy.run_path(str(source),run_name='__main__')
elif len(sys.argv)>1 and sys.argv[1]=='borrow-evidence':
 import runpy
 source=runner.ROOT/runner.CORE/'02_FOUNDRY_ALL_PRODUCTS/parent_products/RETRO_PRODUCTS/R026_S423_S424_EBC/ebc.py'
 sys.argv=[str(source),*sys.argv[2:]]
 sys.path.insert(0,str(source.parent))
 runpy.run_path(str(source),run_name='__main__')
elif len(sys.argv)>1 and sys.argv[1] in ('components','show','check','demo'):
 from maintenance.components import main
 sys.exit(main(sys.argv[1:]))
elif len(sys.argv)>1 and sys.argv[1]=='experiment':
 from maintenance.experiment import execute
 p=argparse.ArgumentParser();p.add_argument('action');p.add_argument('folder');p.add_argument('--entry',default='run_experiment.py');p.add_argument('--timeout',type=float,default=180);args=p.parse_args()
 try:
  result=execute(args.folder,args.entry,args.timeout);print(result);sys.exit(0 if json.loads(result.read_text())['status']=='EXECUTED' else 1)
 except (ValueError,OSError) as e:p.error(str(e))
elif len(sys.argv)>1 and sys.argv[1]=='compare':
 p=argparse.ArgumentParser();p.add_argument('action');p.add_argument('spec');p.add_argument('data');p.add_argument('--output',required=True);args=p.parse_args()
 try:
  result=evaluate(args.spec,args.data)
  # Comparison history is never silently overwritten.
  with Path(args.output).open('x') as f:json.dump(result,f,indent=2)
  print(args.output)
 except (ValueError,OSError) as e:p.error(str(e))
else:sys.exit(runner.main())
