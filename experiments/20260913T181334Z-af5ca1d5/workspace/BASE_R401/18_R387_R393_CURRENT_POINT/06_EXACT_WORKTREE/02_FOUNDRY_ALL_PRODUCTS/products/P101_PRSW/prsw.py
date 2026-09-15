from products.spec_runtime import evaluate_spec_product

PRODUCT_SPEC = {'product_id': 'P101', 'short_name': 'PRSW', 'title': 'Product result — P101_PRSW v0.1', 'parents_raw': 'PRIU + OWS', 'historical_promotion_state': '', 'claim_boundary_raw': 'Importance weights define a target scenario law; they are not probabilities until multiplied by source scenario mass and renormalized. Fragile support blocks the target financing claim.', 'execution_mode': 'selection'}

def evaluate(records, *, baseline=None, budget=None):
    return evaluate_spec_product(PRODUCT_SPEC, records, baseline=baseline, budget=budget)
