from products.spec_runtime import evaluate_spec_product

PRODUCT_SPEC = {'product_id': 'P124', 'short_name': 'HCGD', 'title': 'Product result — P124_HCGD v0.1', 'parents_raw': 'DHCC + CSID', 'historical_promotion_state': '', 'claim_boundary_raw': 'Instrument unavailability is a declared counterfactual; liquidity/default mechanisms are not inferred by DHCC.', 'execution_mode': 'selection'}

def evaluate(records, *, baseline=None, budget=None):
    return evaluate_spec_product(PRODUCT_SPEC, records, baseline=baseline, budget=budget)
