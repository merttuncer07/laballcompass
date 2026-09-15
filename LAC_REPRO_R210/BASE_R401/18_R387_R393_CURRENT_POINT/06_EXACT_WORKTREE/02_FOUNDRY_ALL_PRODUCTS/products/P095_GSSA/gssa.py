from products.spec_runtime import evaluate_spec_product

PRODUCT_SPEC = {'product_id': 'P095', 'short_name': 'GSSA', 'title': 'P095_GSSA — Geometry-Support Shift Audit', 'parents_raw': 'UNEXTRACTED', 'historical_promotion_state': 'UNEXTRACTED', 'claim_boundary_raw': 'Density-ratio audit requires common discrete support and positive source mass in every represented target bin.', 'execution_mode': 'audit'}

def evaluate(records, *, baseline=None, budget=None):
    return evaluate_spec_product(PRODUCT_SPEC, records, baseline=baseline, budget=budget)
