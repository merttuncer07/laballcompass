from products.spec_runtime import evaluate_spec_product

PRODUCT_SPEC = {'product_id': 'P129', 'short_name': 'LIGD', 'title': 'Product result — P129_LIGD v0.1', 'parents_raw': 'SLERM + CSID', 'historical_promotion_state': '', 'claim_boundary_raw': 'Counterfactual signal traces are declared failure scenarios; the product does not infer mitigation reliability from monitoring data.', 'execution_mode': 'selection'}

def evaluate(records, *, baseline=None, budget=None):
    return evaluate_spec_product(PRODUCT_SPEC, records, baseline=baseline, budget=budget)
