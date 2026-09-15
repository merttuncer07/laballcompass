from products.spec_runtime import evaluate_spec_product

PRODUCT_SPEC = {'product_id': 'P090', 'short_name': 'SWDL', 'title': 'P090_SWDL — Support-Weighted Decision Loss', 'parents_raw': 'UNEXTRACTED', 'historical_promotion_state': 'UNEXTRACTED', 'claim_boundary_raw': 'Target importance weights must be externally justified; usable ESS does not prove transportability.', 'execution_mode': 'selection'}

def evaluate(records, *, baseline=None, budget=None):
    return evaluate_spec_product(PRODUCT_SPEC, records, baseline=baseline, budget=budget)
