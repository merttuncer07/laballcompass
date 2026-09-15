from products.spec_runtime import evaluate_spec_product

PRODUCT_SPEC = {'product_id': 'P097', 'short_name': 'BDSD', 'title': 'P097_BDSD — Blackwell-Deduplicated Safeguard Design', 'parents_raw': 'UNEXTRACTED', 'historical_promotion_state': 'UNEXTRACTED', 'claim_boundary_raw': 'Blackwell dominance establishes information redundancy, not identical operational failure modes; the shared evidence-family mapping is a declared design policy.', 'execution_mode': 'audit'}

def evaluate(records, *, baseline=None, budget=None):
    return evaluate_spec_product(PRODUCT_SPEC, records, baseline=baseline, budget=budget)
