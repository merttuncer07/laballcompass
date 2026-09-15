from products.spec_runtime import evaluate_spec_product

PRODUCT_SPEC = {'product_id': 'P132', 'short_name': 'CARA', 'title': 'Product result — P132_CARA v0.1', 'parents_raw': 'CWC + ACRA', 'historical_promotion_state': '', 'claim_boundary_raw': 'Calibration consequence uses the declared target, window, and interval-score scaling; it is not a universal loss function.', 'execution_mode': 'selection'}

def evaluate(records, *, baseline=None, budget=None):
    return evaluate_spec_product(PRODUCT_SPEC, records, baseline=baseline, budget=budget)
