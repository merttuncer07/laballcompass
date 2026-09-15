from products.spec_runtime import evaluate_spec_product

PRODUCT_SPEC = {'product_id': 'P089', 'short_name': 'OCTS', 'title': 'P089_OCTS — Ownership Control Tipping Surface', 'parents_raw': 'OWNM + TDSX', 'historical_promotion_state': 'UNEXTRACTED', 'claim_boundary_raw': 'Voting control follows OWNM threshold propagation. Economic exposure remains separate; control does not imply 100% cash-flow ownership.', 'execution_mode': 'tipping'}

def evaluate(records, *, baseline=None, budget=None):
    return evaluate_spec_product(PRODUCT_SPEC, records, baseline=baseline, budget=budget)
