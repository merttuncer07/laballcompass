from products.spec_runtime import evaluate_spec_product

PRODUCT_SPEC = {'product_id': 'P055', 'short_name': 'SLHA', 'title': 'Synchronization Lock-in Holdout Audit', 'parents_raw': 'SLERM + ACSA', 'execution_mode': 'audit', 'reconstruction_tier': 'NEW_REPLACEMENT_FOR_UNRECOVERABLE_HISTORICAL_ID', 'claim_boundary_raw': 'Historical identity and source were unrecoverable; this is a new composition occupying an archive gap, not recovered history.'}

def evaluate(records, *, baseline=None, budget=None):
    return evaluate_spec_product(PRODUCT_SPEC, records, baseline=baseline, budget=budget)
