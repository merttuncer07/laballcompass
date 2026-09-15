from products.spec_runtime import evaluate_spec_product

PRODUCT_SPEC = {'product_id': 'P096', 'short_name': 'TRIA', 'title': 'P096_TRIA — Transient-Risk Information Acquisition', 'parents_raw': 'UNEXTRACTED', 'historical_promotion_state': 'UNEXTRACTED', 'claim_boundary_raw': 'Channel cost is expressed in the same declared units as flip-index reduction; Gaussian linear update assumptions remain explicit.', 'execution_mode': 'allocation'}

def evaluate(records, *, baseline=None, budget=None):
    return evaluate_spec_product(PRODUCT_SPEC, records, baseline=baseline, budget=budget)
