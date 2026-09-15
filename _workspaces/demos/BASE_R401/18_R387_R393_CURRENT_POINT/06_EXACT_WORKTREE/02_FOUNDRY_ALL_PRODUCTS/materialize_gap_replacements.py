from __future__ import annotations

from pathlib import Path


ROOT=Path(__file__).resolve().parent/'products'
SPECS=[
('P009','URAI','Uncertainty-Routed Acquisition Interface','DFDPE + AICC','allocation'),
('P010','DPHO','Deployment Policy Holdout','CDBL + ACSA','audit'),
('P011','IDLG','Integrality Decision-Loss Gate','RIC + DLEW','selection'),
('P020','REDT','Relational Evidence Discrepancy Tipping','REL + TDSX','tipping'),
('P021','MRIA','Model-Reduction Information Acquisition','TWMR + AICC','allocation'),
('P022','AFHA','Architecture Failure Holdout Audit','MFPA + ACSA','audit'),
('P023','COST','Causal Overlap Sensitivity Tipping','OTE + TDSX','tipping'),
('P024','TFRD','Time-Frequency Reporting Decision','TFLD + DLEW','selection'),
('P051','ICHA','Incidence Choice Holdout Audit','LGID + ACSA','audit'),
('P052','VCTS','Volcano Coupling Tipping Surface','VICO + TDSX','tipping'),
('P053','GWDA','Geometry-Weighted Decision Audit','WBDP + DLEW','audit'),
('P054','MCSA','Monotonicity Certificate Sampling Acquisition','MCSC + AICC','allocation'),
('P055','SLHA','Synchronization Lock-in Holdout Audit','SLERM + ACSA','audit'),
('P056','CFTS','Circular Flow Tipping Surface','HFAD + TDSX','tipping'),
('P069','PSHA','Persuasion Strategy Holdout Audit','BPISD + ACSA','audit'),
('P070','UTIA','Unequal-Transport Information Acquisition','UTDIM + AICC','allocation'),
('P071','HPDT','Hidden Population Decision Tipping','MLHPE + TDSX','tipping'),
('P072','RMHA','Reduction Model Holdout Audit','BRED + ACSA','audit'),
('P073','FCDL','Fabrication Certificate Decision Loss','FCMS + DLEW','selection'),
('P074','PBIA','Percolation Breakthrough Information Acquisition','PCBE + AICC','allocation'),
('P106','RCHA','Reporting Contract Holdout Audit','SRCD + ACSA','audit'),
('P107','LDLA','Lumpability Decision Loss Audit','SALC + DLEW','audit'),
('P108','OSTS','Observability Sensitivity Tipping Surface','CORMA + TDSX','tipping'),
('P109','CCIA','Conservation-Calibrated Information Acquisition','CSDC + AICC','allocation'),
('P110','MBTS','Mortgage Burnout Tipping Surface','MBPF + TDSX','tipping'),
('P111','LVAI','Liquidity Verification Acquisition Interface','LCM + AICC','allocation'),
('P112','RTTS','Restart Threshold Tipping Surface','RTO + TDSX','tipping'),
('P113','QDLA','Quasineutral Decision-Loss Audit','APTC + DLEW','audit'),
]

for product_id,short,title,parents,mode in SPECS:
    target=ROOT/f'{product_id}_{short}'
    target.mkdir(parents=True,exist_ok=True)
    module=short.lower()
    spec={'product_id':product_id,'short_name':short,'title':title,'parents_raw':parents,'execution_mode':mode,'reconstruction_tier':'NEW_REPLACEMENT_FOR_UNRECOVERABLE_HISTORICAL_ID','claim_boundary_raw':'Historical identity and source were unrecoverable; this is a new composition occupying an archive gap, not recovered history.'}
    (target/'__init__.py').write_text(f'from .{module} import *\n',encoding='utf-8')
    (target/f'{module}.py').write_text(
        'from products.spec_runtime import evaluate_spec_product\n\n'
        f'PRODUCT_SPEC = {spec!r}\n\n'
        'def evaluate(records, *, baseline=None, budget=None):\n'
        '    return evaluate_spec_product(PRODUCT_SPEC, records, baseline=baseline, budget=budget)\n',encoding='utf-8')
    (target/f'test_{module}.py').write_text(
        f'from .{module} import *\n\n'
        "R=[{'name':'a','score':1,'value':1,'cost':1,'parameter':0,'decision':False,'selection_score':2,'protected_score':0},{'name':'b','score':2,'value':2,'cost':1,'parameter':1,'decision':True,'selection_score':1,'protected_score':3}]\n"
        "def kwargs(): return {'budget':1} if PRODUCT_SPEC['execution_mode']=='allocation' else ({'baseline':R[0]} if PRODUCT_SPEC['execution_mode']=='tipping' else {})\n"
        f"def test_gap_identity_explicit(): assert PRODUCT_SPEC['product_id']=='{product_id}'\n"
        "def test_new_replacement_tier_explicit(): assert evaluate(R,**kwargs())['reconstruction_tier']=='NEW_REPLACEMENT_FOR_UNRECOVERABLE_HISTORICAL_ID'\n"
        "def test_parent_composition_declared(): assert '+' in PRODUCT_SPEC['parents_raw']\n"
        "def test_execution_returns_status(): assert evaluate(R,**kwargs())['status']\n",encoding='utf-8')
    (target/'RECONSTRUCTION_STATUS.md').write_text(
        f'# {product_id} archive-gap replacement\n\nThe rescue contains no name, parent, result, code, test, or benchmark for the historical ID. '
        f'This directory therefore contains the newly designed **{short} — {title}** ({parents}), not a fabricated recovery claim.\n',encoding='utf-8')

print(f'materialized {len(SPECS)} explicit gap replacements')
