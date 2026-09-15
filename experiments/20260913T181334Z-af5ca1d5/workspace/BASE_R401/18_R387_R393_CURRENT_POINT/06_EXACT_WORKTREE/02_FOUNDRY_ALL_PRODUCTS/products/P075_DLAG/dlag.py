from products.spec_runtime import evaluate_spec_product

PRODUCT_SPEC = {'product_id': 'P075', 'short_name': 'DLAG', 'title': 'Decision-Loss-Aware Lumpability Guard', 'parents_raw': 'UNEXTRACTED', 'historical_promotion_state': 'PROMOTED v0.1', 'claim_boundary_raw': 'Exact strong lumpability is a transition-law certificate only. DLAG adds a declared utility matrix and regret tolerance; it does not claim a partition is decision-safe for unmodeled actions or utilities.', 'execution_mode': 'audit'}

def evaluate(records, *, baseline=None, budget=None):
    return evaluate_spec_product(PRODUCT_SPEC, records, baseline=baseline, budget=budget)
