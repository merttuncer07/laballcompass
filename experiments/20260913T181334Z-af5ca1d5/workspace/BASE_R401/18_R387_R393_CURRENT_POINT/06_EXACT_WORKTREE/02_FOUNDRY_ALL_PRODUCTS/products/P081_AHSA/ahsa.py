from products.spec_runtime import evaluate_spec_product

PRODUCT_SPEC = {'product_id': 'P081', 'short_name': 'AHSA', 'title': 'Adaptive Hedge Selection Audit', 'parents_raw': 'UNEXTRACTED', 'historical_promotion_state': 'PROMOTED v0.1', 'claim_boundary_raw': 'AHSA diagnoses adaptive hedge-selection regret on the declared protected sample. It does not guarantee future market performance or model transaction costs beyond the supplied DHCC loss contract.', 'execution_mode': 'audit'}

def evaluate(records, *, baseline=None, budget=None):
    return evaluate_spec_product(PRODUCT_SPEC, records, baseline=baseline, budget=budget)
