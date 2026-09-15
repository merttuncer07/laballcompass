"""Run every parent and Foundry test, including previously excluded REIG pytest tests."""
from pathlib import Path
import argparse,fnmatch,json,sys
BASE=next(p for p in Path(__file__).resolve().parents if (p/'maintenance/runner.py').exists())
sys.path.insert(0,str(BASE))
from maintenance import runner

def main():
 p=argparse.ArgumentParser();p.add_argument('--target',default='*');p.add_argument('--timeout',type=float,default=180);a=p.parse_args()
 targets=[t for t in runner.discover('parents')+runner.discover('foundry') if fnmatch.fnmatchcase(t.id,a.target)]
 try:path=runner.run(targets,timeout=a.timeout,profile='parents+foundry')
 except ValueError as e:p.error(str(e))
 print(path);return int(json.loads(path.read_text())['status']!='PASS')
if __name__=='__main__':sys.exit(main())
