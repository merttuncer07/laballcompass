from __future__ import annotations
import functools, importlib.util, pathlib, sys, unittest
import numpy as np
from sacdlw import support_covariance_decision_loss_workbench

ROOT=pathlib.Path(__file__).resolve().parents[3]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(spec); sys.modules[name]=m; spec.loader.exec_module(m); return m
SACPS=load('sacps_v2p051',ROOT/'02_FOUNDRY_ALL_PRODUCTS/parent_products/RETRO_PRODUCTS/R037_SUPPORT_COVARIANCE_SACPS/sacps.py')
DLEW=load('dlew_v2p051',ROOT/'02_FOUNDRY_ALL_PRODUCTS/parent_products/RETRO_PRODUCTS/R044_DECISION_LOSS_DLEW/dlew.py')
ACTIONS=np.array([[1.,0.,0.],[0.,1.,0.],[.5,.5,0.],[0.,0.,1.]])
INITIAL=np.array([.5,.5,0.])
TRUE_COV=np.diag([.0004,.0004,.001])
MEAN=np.array([.005,.005,.004])

def dataset(seed=0,n_train=80,n_cal=1000,n_val=1000,spurious_correlation=-.95):
    rng=np.random.default_rng(seed)
    tr=rng.multivariate_normal(MEAN,TRUE_COV,size=n_train)
    cal=rng.multivariate_normal(MEAN,TRUE_COV,size=n_cal)
    va=rng.multivariate_normal(MEAN,TRUE_COV,size=n_val)
    a_tr=tr+rng.normal(scale=.020,size=tr.shape)
    a_va=va+rng.normal(scale=.020,size=va.shape)
    b_tr=np.tile(MEAN,(n_train,1))+rng.normal(scale=.005,size=tr.shape)
    b_va=np.tile(MEAN,(n_val,1))+rng.normal(scale=.005,size=va.shape)
    # Separate risk-estimation sample: its first two marginals keep the same
    # scale but carry a tunable finite-sample nuisance edge. The declared
    # support and independent calibration sample say that edge is unsupported.
    rho=float(spurious_correlation)
    if not -0.99 <= rho <= 0.99: raise ValueError('spurious_correlation must lie in [-.99,.99]')
    shared=rng.normal(scale=.020,size=n_train)
    e0=rng.normal(scale=.020,size=n_train); e1=rng.normal(scale=.020,size=n_train)
    e2=rng.normal(scale=np.sqrt(.001),size=n_train)
    magnitude=abs(rho)
    x0=np.sqrt(magnitude)*shared+np.sqrt(1-magnitude)*e0
    x1=np.sign(rho if rho else 1.0)*np.sqrt(magnitude)*shared+np.sqrt(1-magnitude)*e1
    risk_train=np.column_stack((x0,x1,e2))+MEAN
    return {'A_signal':a_tr,'B_stable':b_tr},tr,{'A_signal':a_va,'B_stable':b_va},va,risk_train,cal,va

def run(*,dense=False,risk_aversion=40.,seed=0,support_limit=.12,spurious_correlation=-.95):
    tp,ty,vp,vy,rt,cal,rv=dataset(seed=seed,spurious_correlation=spurious_correlation)
    support=np.ones((3,3),dtype=bool) if dense else np.eye(3,dtype=bool)
    return support_covariance_decision_loss_workbench(
        DLEW,SACPS.estimate_support_aware_covariance,tp,ty,vp,vy,ACTIONS,rt,rv,support,
        initial_action_exposure=INITIAL,support_calibration_returns=cal,shrinkage_grid=[0.],
        risk_aversion=risk_aversion,transaction_cost=0.,maximum_calibration_off_support_correlation=support_limit,
    )

@functools.lru_cache(maxsize=None)
def working(): return run()

class T(unittest.TestCase):
    def test_working_region_changes_selected_model(self):
        r=working(); self.assertEqual(r['candidate_selected_model'],'A_signal'); self.assertEqual(r['control_selected_model'],'B_stable')
    def test_working_region_improves_common_reference_regret(self): self.assertGreater(working()['validation_reference_regret_gain_vs_raw_covariance'],.001)
    def test_working_region_changes_actions(self): self.assertFalse(working()['candidate_actions_equal_control'])
    def test_off_support_noise_is_removed(self):
        r=working(); self.assertGreater(r['raw_off_support_max_abs_covariance'],0.); self.assertAlmostEqual(np.max(np.abs(np.asarray(r['supported_covariance'])-np.diag(np.diag(r['supported_covariance'])))),0.,places=14)
    def test_dense_support_zero_shrinkage_collapses_to_raw_control(self):
        r=run(dense=True,support_limit=None); self.assertTrue(r['supported_equals_raw_covariance']); self.assertEqual(r['candidate_selected_model'],r['control_selected_model']); self.assertTrue(r['candidate_actions_equal_control']); self.assertAlmostEqual(r['validation_reference_regret_gain_vs_raw_covariance'],0.,places=14)
    def test_zero_risk_aversion_collapses_to_parent_dlew_selection(self):
        r=run(risk_aversion=0.); self.assertEqual(r['candidate_selected_model'],r['parent_dlew_selected_model']); self.assertEqual(r['control_selected_model'],r['parent_dlew_selected_model']); self.assertTrue(r['candidate_actions_equal_control'])
    def test_wrong_support_abstains_when_calibration_contradicts_it(self):
        tp,ty,vp,vy,rt,cal,rv=dataset(seed=0); rng=np.random.default_rng(9); z=rng.normal(size=1000); cal[:,1]=.95*z+.05*rng.normal(size=1000); cal[:,0]=z
        r=support_covariance_decision_loss_workbench(DLEW,SACPS.estimate_support_aware_covariance,tp,ty,vp,vy,ACTIONS,rt,rv,np.eye(3,dtype=bool),initial_action_exposure=INITIAL,support_calibration_returns=cal,shrinkage_grid=[0.],risk_aversion=20.,maximum_calibration_off_support_correlation=.2)
        self.assertEqual(r['status'],'ABSTAIN_SUPPORT_CONTRADICTED_BY_CALIBRATION')
    def test_support_contradiction_check_requires_calibration(self):
        tp,ty,vp,vy,rt,cal,rv=dataset();
        with self.assertRaises(ValueError): support_covariance_decision_loss_workbench(DLEW,SACPS.estimate_support_aware_covariance,tp,ty,vp,vy,ACTIONS,rt,rv,np.eye(3,dtype=bool),initial_action_exposure=INITIAL,risk_aversion=20.,maximum_calibration_off_support_correlation=.2)
    def test_bad_support_rejected(self):
        tp,ty,vp,vy,rt,cal,rv=dataset(); bad=np.eye(3,dtype=bool); bad[0,1]=True
        with self.assertRaises(ValueError): support_covariance_decision_loss_workbench(DLEW,SACPS.estimate_support_aware_covariance,tp,ty,vp,vy,ACTIONS,rt,rv,bad,initial_action_exposure=INITIAL)
    def test_prediction_key_mismatch_rejected(self):
        tp,ty,vp,vy,rt,cal,rv=dataset(); vp.pop('B_stable')
        with self.assertRaises(ValueError): support_covariance_decision_loss_workbench(DLEW,SACPS.estimate_support_aware_covariance,tp,ty,vp,vy,ACTIONS,rt,rv,np.eye(3,dtype=bool),initial_action_exposure=INITIAL)
    def test_negative_risk_rejected(self):
        tp,ty,vp,vy,rt,cal,rv=dataset();
        with self.assertRaises(ValueError): support_covariance_decision_loss_workbench(DLEW,SACPS.estimate_support_aware_covariance,tp,ty,vp,vy,ACTIONS,rt,rv,np.eye(3,dtype=bool),initial_action_exposure=INITIAL,risk_aversion=-1.)
    def test_deterministic(self): self.assertEqual(working(),working())

if __name__=='__main__': unittest.main()
