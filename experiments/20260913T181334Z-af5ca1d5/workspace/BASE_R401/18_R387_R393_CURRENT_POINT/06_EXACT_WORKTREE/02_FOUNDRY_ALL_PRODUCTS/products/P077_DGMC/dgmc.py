from products.spec_runtime import evaluate_spec_product

PRODUCT_SPEC = {'product_id': 'P077', 'short_name': 'DGMC', 'title': 'Deliverability-Gated Market Clearing', 'parents_raw': 'UNEXTRACTED', 'historical_promotion_state': 'PROMOTED v0.1', 'claim_boundary_raw': 'CDBL quantities are physical/operational deployability under the declared network. DGMC does not infer strategic availability, forced outages, or offer-price changes unless explicitly represented upstream.', 'execution_mode': 'selection'}

def evaluate(records, *, baseline=None, budget=None):
    return evaluate_spec_product(PRODUCT_SPEC, records, baseline=baseline, budget=budget)
