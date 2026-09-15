import json
import numpy as np
from edsanp import SupportEvidence, construct_effective_diversity_gated_portfolio, compare_gated_with_raw_on_fresh_returns


def sparse_covariance():
    covariance=np.eye(8)*0.0004
    for i in range(0,8,2):
        covariance[i,i]=0.0005+0.00005*i; covariance[i+1,i+1]=0.0006+0.00004*i
        covariance[i,i+1]=covariance[i+1,i]=0.00020
    for i,j,v in [(0,2,.00008),(2,4,.00006),(4,6,.00005)]: covariance[i,j]=covariance[j,i]=v
    return covariance

rng=np.random.default_rng(20260825); cov=sparse_covariance(); data=rng.multivariate_normal(np.zeros(8),cov,size=535)
train,val,fresh=data[:35],data[35:185],data[185:]; mask=np.abs(cov)>0
pairs=[(i,j) for i in range(8) for j in range(i+1,8)]
kwargs=dict(factor_loadings=np.array([[-1.,-.7,-.4,-.1,.1,.4,.7,1.]]),target_factor_exposure=np.array([0.]),lower_bounds=0.,upper_bounds=.35,risk_aversion=4.)
def ev(rho): return {p:SupportEvidence(100,rho) for p in pairs}
low=construct_effective_diversity_gated_portfolio(train,mask,ev(.001),np.zeros(8),covariance_validation_returns=val,min_effective_count=20,max_variance_inflation=2,**kwargs)
high=construct_effective_diversity_gated_portfolio(train,mask,ev(.05),np.zeros(8),covariance_validation_returns=val,min_effective_count=20,max_variance_inflation=10,**kwargs)
collective=construct_effective_diversity_gated_portfolio(train,mask,{p:SupportEvidence(200,.009) for p in pairs},np.zeros(8),min_effective_count=10,max_variance_inflation=2,pairwise_threshold=.01,**kwargs)
out={
 'low_dependence':{'route':low.route,'first_check':low.support_checks[0].to_dict(),'fresh':compare_gated_with_raw_on_fresh_returns(low,train,np.zeros(8),fresh,**kwargs)},
 'high_dependence':{'route':high.route,'first_check':high.support_checks[0].to_dict()},
 'pairwise_small_collective_large':{'route':collective.route,'first_check':collective.support_checks[0].to_dict()},
 'claim_scope':'deterministic development adapter shell; effective-diversity gate does not certify support truth or real-world portfolio performance'
}
print(json.dumps(out,indent=2))
