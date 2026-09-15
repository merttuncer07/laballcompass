from products.spec_runtime import evaluate_spec_product

PRODUCT_SPEC = {'product_id': 'P100', 'short_name': 'WICA', 'title': 'Product result — P100_WICA v0.1', 'parents_raw': 'OWS + BICC', 'historical_promotion_state': '', 'claim_boundary_raw': 'BICC global bounds remain assumption-conditional and observed replacement effects are not proof of worst-case global influence.', 'execution_mode': 'selection'}

def evaluate(records, *, baseline=None, budget=None):
    return evaluate_spec_product(PRODUCT_SPEC, records, baseline=baseline, budget=budget)
