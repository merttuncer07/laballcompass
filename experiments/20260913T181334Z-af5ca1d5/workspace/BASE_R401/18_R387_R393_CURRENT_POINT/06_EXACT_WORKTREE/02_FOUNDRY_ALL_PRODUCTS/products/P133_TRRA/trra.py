from products.spec_runtime import evaluate_spec_product

PRODUCT_SPEC = {'product_id': 'P133', 'short_name': 'TRRA', 'title': 'Product result — P133_TRRA v0.1', 'parents_raw': 'DTRM + ACRA', 'historical_promotion_state': '', 'claim_boundary_raw': 'Direction scores depend on the declared linearized dynamics, uncertainty radius, horizon, and decision gap.', 'execution_mode': 'selection'}

def evaluate(records, *, baseline=None, budget=None):
    return evaluate_spec_product(PRODUCT_SPEC, records, baseline=baseline, budget=budget)
