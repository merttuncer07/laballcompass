from products.spec_runtime import evaluate_spec_product

PRODUCT_SPEC = {'product_id': 'P076', 'short_name': 'MCFS', 'title': 'Market-Clearing Fragility Surface', 'parents_raw': 'UNEXTRACTED', 'historical_promotion_state': 'PROMOTED v0.1', 'claim_boundary_raw': 'The tipping point is conditional on the declared offer stack, fixed offer prices/quantities, scarcity-price rule, and finite demand grid. It is not a forecast of strategic bidding or endogenous supply entry.', 'execution_mode': 'tipping'}

def evaluate(records, *, baseline=None, budget=None):
    return evaluate_spec_product(PRODUCT_SPEC, records, baseline=baseline, budget=budget)
