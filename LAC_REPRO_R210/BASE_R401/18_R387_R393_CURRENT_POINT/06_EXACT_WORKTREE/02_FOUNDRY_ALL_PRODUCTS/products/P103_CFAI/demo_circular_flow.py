"""An explicit synthetic counterexample to ranking flow edges by amount alone."""
import json
from cfai import evaluate

if __name__ == '__main__':
    result = evaluate({'node_count':4, 'edges':[[0,1],[1,2],[2,0],[2,3]],
        'edge_names':['cycle_a','cycle_b','cycle_c','large_bridge'],
        'base_flows':[[10.,10.,10.,1000.]], 'replacement_flows':[[0.,9.,9.5,0.]], 'budget':1.})
    print(json.dumps(result,indent=2,allow_nan=False))
