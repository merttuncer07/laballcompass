"""Run legacy unittest suites and emit structured counts without parsing console text."""
import json,sys,unittest
from pathlib import Path

def main():
 output=Path(sys.argv[1]);pattern=sys.argv[2]
 sys.path.insert(0,str(Path.cwd()))
 suite=unittest.defaultTestLoader.discover('.',pattern=pattern)
 result=unittest.TextTestRunner(verbosity=2).run(suite)
 report={'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'expected_failures':len(result.expectedFailures),'unexpected_successes':len(result.unexpectedSuccesses),'successful':result.wasSuccessful()}
 output.write_text(json.dumps(report,indent=2))
 return 0 if result.wasSuccessful() else 1
if __name__=='__main__':sys.exit(main())
