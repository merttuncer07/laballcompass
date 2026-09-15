from __future__ import annotations
import json
from pathlib import Path
from test_mfpd import case


def main():
    near_high=case(-.03,.25,2,70,rho=.9)
    near_low=case(-.03,.25,2,70,rho=.01)
    far=case(-.5,.05,4,90,rho=.9)
    proxy_reduction=None
    if near_high.variance_proxy is not None and near_low.variance_proxy:
        proxy_reduction=1.0-near_high.variance_proxy/near_low.variance_proxy
    result={
        'product_id':'V2P003_MFPD',
        'composition':'LCB-K048 MultiFidelityBudgetControllerV0 -> FOUNDRY:P144 DPAI',
        'near_boundary_high_correlation':near_high.to_dict(),
        'near_boundary_low_correlation':near_low.to_dict(),
        'far_stable_case':far.to_dict(),
        'multifidelity_variance_proxy_reduction_vs_fine_only':proxy_reduction,
        'claim_boundary':'variance_proxy is K048 program-design proxy only; not persistence uncertainty, action loss, or scientific validation',
    }
    out=Path(__file__).with_name('BENCHMARK_RESULT.json')
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__=='__main__':
    main()
