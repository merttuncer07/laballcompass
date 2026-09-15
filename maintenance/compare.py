"""Paired comparison contract. A software pass is never a scientific promotion."""
import csv,hashlib,json,math,random,statistics
from pathlib import Path

def evaluate(spec_path,data_path):
 spec_path=Path(spec_path);data_path=Path(data_path);spec=json.loads(spec_path.read_text())
 for field in ('candidate','baseline','metric','unit','direction','cases','replicates','replication_kind'):
  if field not in spec:raise ValueError('Missing comparison field: '+field)
 if spec['candidate']==spec['baseline']:raise ValueError('Candidate and baseline must differ')
 if spec['direction'] not in ('minimize','maximize'):raise ValueError('direction must be minimize/maximize')
 if spec['replication_kind'] not in ('independent_blocks','deterministic','timing_repeats'):raise ValueError('Declare replication_kind explicitly')
 cases=spec['cases'];reps=spec['replicates']
 for label,items in [('cases',cases),('replicates',reps)]:
  if not items or any(not isinstance(x,str) or not x for x in items) or len(items)!=len(set(items)):raise ValueError(label+' must be unique nonempty string IDs')
 methods=[spec['candidate'],spec['baseline']];values={}
 with data_path.open(newline='') as f:
  for row in csv.DictReader(f):
   try:
    key=(row['method'],row['case'],row['replicate'])
    if key[0] not in methods or key[1] not in cases or key[2] not in reps:raise ValueError('Undeclared method, case or replicate')
    if key in values:raise ValueError('Duplicate observation: '+str(key))
    v=float(row['value'])
    if not math.isfinite(v):raise ValueError('Non-finite metric')
    values[key]=v
   except KeyError as e:raise ValueError('Missing CSV column: '+str(e))
 required={(m,c,r) for m in methods for c in cases for r in reps}
 if set(values)!=required:raise ValueError('Incomplete paired comparison: '+str(len(required-set(values)))+' observations missing')
 sign=1 if spec['direction']=='maximize' else -1
 gains={c:[sign*(values[(methods[0],c,r)]-values[(methods[1],c,r)]) for r in reps] for c in cases}
 blocks=[statistics.mean(gains[c][i] for c in cases) for i in range(len(reps))]
 result={'scope':'declared_metric_on_declared_cases_only','candidate':methods[0],'baseline':methods[1],'metric':spec['metric'],'unit':spec['unit'],'direction':spec['direction'],'cases':len(cases),'replication_blocks':len(reps),'replication_kind':spec['replication_kind'],'mean_gain':statistics.mean(blocks),'per_case_mean_gain':{c:statistics.mean(v) for c,v in gains.items()},'worsened_cases':[c for c,v in gains.items() if statistics.mean(v)<0],'promotion':'NOT_ASSESSED','spec_sha256':hashlib.sha256(spec_path.read_bytes()).hexdigest(),'data_sha256':hashlib.sha256(data_path.read_bytes()).hexdigest(),'interval':None}
 if spec['replication_kind']=='independent_blocks' and len(reps)>=5:
  rng=random.Random(0);n=len(blocks);samples=sorted(statistics.mean(blocks[rng.randrange(n)] for _ in range(n)) for _ in range(5000))
  result['interval']={'method':'paired block percentile bootstrap','level':0.95,'low':samples[124],'high':samples[4874],'resamples':5000,'seed':0,'assumption':'Declared replication blocks are independent. Cases are fixed; same blocks are resampled jointly across all cases. Small-sample coverage is not guaranteed.'}
 else:result['interval_note']='Uncertainty withheld: deterministic/timing repetitions or fewer than five declared independent blocks.'
 result['limits']=['Manifest hashes bind supplied inputs; they do not prove preregistration or that omitted runs do not exist.','No generalization to untested cases, scientific novelty, or audit effectiveness is established.','Replicate IDs do not prove independence; this is a declared experimental design assumption.']
 return result
