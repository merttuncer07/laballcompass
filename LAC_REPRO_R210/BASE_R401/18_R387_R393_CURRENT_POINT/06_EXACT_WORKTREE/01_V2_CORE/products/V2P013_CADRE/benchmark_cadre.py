import json
from pathlib import Path
from cadre import GaussianArm, compression_aware_dre
def a(n,m,v=.04): return GaussianArm(n,m,v,.2,0)
compressed=[a('A',1),a('B',.98),a('C',.2,1)]
full=[a('A',.96),a('B',1.03),a('C',.2,1)]
r=compression_aware_dre(compressed_arms=compressed,compression_error_bounds={'A':.05,'B':.05,'C':0},remaining_decisions=10,full_resolution_arms=full)
out={'model_version':'V2P013_CADRE_V1','mechanism_removing_comparator':'DRE executed on compressed states without P091-style compression tipping certificate','result':r.to_dict(),'blind_choice':r.compressed_choice,'guarded_choice':r.final_choice,'evidence_boundary':'deterministic compressed-vs-full Gaussian-arm mechanism benchmark only'}
Path(__file__).with_name('BENCHMARK_RESULT.json').write_text(json.dumps(out,indent=2)+'\n'); print(json.dumps(out,indent=2))
