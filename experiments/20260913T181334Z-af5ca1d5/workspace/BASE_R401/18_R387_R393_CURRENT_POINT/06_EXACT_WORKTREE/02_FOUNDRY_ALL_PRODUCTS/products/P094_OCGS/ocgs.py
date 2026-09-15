from products.spec_runtime import evaluate_spec_product

PRODUCT_SPEC = {'product_id': 'P094', 'short_name': 'OCGS', 'title': 'P094_OCGS — Ownership Control Guard Selection', 'parents_raw': 'UNEXTRACTED', 'historical_promotion_state': 'UNEXTRACTED', 'claim_boundary_raw': 'Failure probabilities and safeguard coverages are declared inputs, not estimated by OWNM.', 'execution_mode': 'audit'}

def evaluate(records, *, baseline=None, budget=None):
    return evaluate_spec_product(PRODUCT_SPEC, records, baseline=baseline, budget=budget)
