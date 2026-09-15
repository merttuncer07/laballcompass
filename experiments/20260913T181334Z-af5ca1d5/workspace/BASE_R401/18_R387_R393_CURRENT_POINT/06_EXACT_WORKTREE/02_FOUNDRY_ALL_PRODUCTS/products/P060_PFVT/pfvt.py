from products.spec_runtime import evaluate_spec_product

PRODUCT_SPEC = {'product_id': 'P060', 'short_name': 'PFVT', 'title': 'P060 PFVT v0.1 — Protected-Financing Viability Tipping', 'parents_raw': 'PRIU → TDSX. Each point on the declared funded-asset-value / promised-repayment surface is audited across every priority insertion. A point passes only when the same insertion both meets lender recovery requirements and leaves every existing claim no worse off.', 'historical_promotion_state': 'WORKING_COMPOSITION / RESTRUCTURING-TIPPING BENCHMARK', 'claim_boundary_raw': '', 'execution_mode': 'tipping'}

def evaluate(records, *, baseline=None, budget=None):
    return evaluate_spec_product(PRODUCT_SPEC, records, baseline=baseline, budget=budget)
