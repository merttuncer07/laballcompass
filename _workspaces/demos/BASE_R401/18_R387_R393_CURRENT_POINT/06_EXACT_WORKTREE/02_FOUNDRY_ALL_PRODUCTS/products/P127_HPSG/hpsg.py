from products.spec_runtime import evaluate_spec_product

PRODUCT_SPEC = {'product_id': 'P127', 'short_name': 'HPSG', 'title': 'Product result — P127_HPSG v0.1', 'parents_raw': 'MLHPE + CSID', 'historical_promotion_state': '', 'claim_boundary_raw': 'Source degradation is a declared stress scenario, not an inferred real-world list failure probability.', 'execution_mode': 'selection'}

def evaluate(records, *, baseline=None, budget=None):
    return evaluate_spec_product(PRODUCT_SPEC, records, baseline=baseline, budget=budget)
