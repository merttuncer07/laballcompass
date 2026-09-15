from products.spec_runtime import evaluate_spec_product

PRODUCT_SPEC = {'product_id': 'P080', 'short_name': 'RAMR', 'title': 'Resilience-Aware Measurement Resolution', 'parents_raw': 'UNEXTRACTED', 'historical_promotion_state': 'PROMOTED v0.1', 'claim_boundary_raw': 'Exposure×recovery is a prioritization proxy, not an expected monetary loss. Mode identity and consequence projection remain conditional on the supplied transition and consequence model.', 'execution_mode': 'selection'}

def evaluate(records, *, baseline=None, budget=None):
    return evaluate_spec_product(PRODUCT_SPEC, records, baseline=baseline, budget=budget)
