from products.spec_runtime import evaluate_spec_product

PRODUCT_SPEC = {'product_id': 'P111', 'short_name': 'LVAI', 'title': 'Liquidity Verification Acquisition Interface', 'parents_raw': 'LCM + AICC', 'execution_mode': 'allocation', 'reconstruction_tier': 'NEW_REPLACEMENT_FOR_UNRECOVERABLE_HISTORICAL_ID', 'claim_boundary_raw': 'Historical identity and source were unrecoverable; this is a new composition occupying an archive gap, not recovered history.'}

def evaluate(records, *, baseline=None, budget=None):
    return evaluate_spec_product(PRODUCT_SPEC, records, baseline=baseline, budget=budget)
