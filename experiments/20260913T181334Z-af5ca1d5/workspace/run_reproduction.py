"""Restored entry point; original implementation is preserved in restoration/source.patch."""
from pathlib import Path
import argparse,fnmatch,json,sys
BASE=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(BASE))
from maintenance import runner

def main():
 p=argparse.ArgumentParser(description='LabAllCompass restored reproduction runner')
 p.add_argument('--profile',choices=['integrity','active','full','all','parents','foundry','recovered'],default='active')
 p.add_argument('--target',default='*');p.add_argument('--timeout',type=float,default=180);a=p.parse_args()
 if a.profile=='integrity':
  import verify_package
  return verify_package.main()
 targets=[t for t in runner.discover(a.profile) if fnmatch.fnmatchcase(t.id,a.target)]
 try:path=runner.run(targets,timeout=a.timeout,profile=a.profile)
 except ValueError as e:p.error(str(e))
 print(path);return int(json.loads(path.read_text())['status']!='PASS')
if __name__=='__main__':sys.exit(main())
