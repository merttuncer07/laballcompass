from products.spec_runtime import evaluate_spec_product

PRODUCT_SPEC = {'product_id': 'P122', 'short_name': 'CAGD', 'title': 'Product result — P122_CAGD v0.1', 'parents_raw': 'CCVC + CSID', 'historical_promotion_state': '', 'claim_boundary_raw': 'The consequence scaling from negative viability margin is declared and local to the audited boundary state.', 'execution_mode': 'audit'}

def evaluate(records, *, baseline=None, budget=None):
    return evaluate_spec_product(PRODUCT_SPEC, records, baseline=baseline, budget=budget)
