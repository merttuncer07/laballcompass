import numpy as np
from v2p054_cadsbc import candidate as c54, removal_control as r54
from v2p055_dlsaicc import Model,candidate as c55,removal_control as r55
from v2p056_sacrdsbc import support_covariance,robust_merge,nominal_control
from v2p057_reoc import select,removal_control,actual_task_score
from v2p058_sacatrc import choose_eviction

def run():
    a=c54([10,1],4); b=r54([10,1],4); assert a.weighted_regret < b.weighted_regret
    models=[Model('rmse',.1,.8,1.0),Model('decision',.2,.1,.1)]
    assert c55(models,.2,.1).selected_model=='decision'; assert r55(models,.2,.1).selected_model=='rmse'
    errs=np.array([[1,0],[0,1],[1,1],[2,0]],float); cov=support_covariance(errs,np.array([[1,1],[1,1]],float)); assert cov.shape==(2,2)
    stress=np.eye(2)*0.10
    assert nominal_control([.5,.5],[.55,.45],.08) and not robust_merge([.5,.5],[.55,.45],stress,.08).merge
    H=np.array([[1,0],[0,1],[.8,.8]],float); s=select([10,1],H,1); ctl=removal_control(H,1); assert s.sensors!=ctl.sensors or s.score!=ctl.score
    losses=[.10,.11,.30]; fp=[[1,0],[.95,0.05],[0,1]]; full=np.ones((2,2)); diag=np.eye(2)
    e=choose_eviction(losses,fp,full,.02); e0=choose_eviction(losses,fp,diag,.02); assert e0.index==0; assert e.index in e.safe_set
    print('RECOVERED_REFERENCE_CONTRACTS PASS')
if __name__=='__main__': run()


def test_recovered_contracts():
    run()
