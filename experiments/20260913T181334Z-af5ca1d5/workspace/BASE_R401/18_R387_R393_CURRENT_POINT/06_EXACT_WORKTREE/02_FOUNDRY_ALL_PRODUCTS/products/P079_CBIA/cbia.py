from products.spec_runtime import evaluate_spec_product

PRODUCT_SPEC = {'product_id': 'P079', 'short_name': 'CBIA', 'title': 'Calibrated Boundary Information Acquisition', 'parents_raw': 'UNEXTRACTED', 'historical_promotion_state': 'PROMOTED v0.1', 'claim_boundary_raw': 'The interval is a calibration object, not a posterior probability of action change. Skipping acquisition is certified only relative to the declared action functions and calibrated interval shell.', 'execution_mode': 'allocation'}

def evaluate(records, *, baseline=None, budget=None):
    return evaluate_spec_product(PRODUCT_SPEC, records, baseline=baseline, budget=budget)
