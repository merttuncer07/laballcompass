from products.spec_runtime import evaluate_spec_product

PRODUCT_SPEC = {'product_id': 'P098', 'short_name': 'SAHA', 'title': 'Product result — P098_SAHA v0.1', 'parents_raw': 'SCE + ACSA', 'historical_promotion_state': '', 'claim_boundary_raw': 'v0.1 deliberately fixes outcome, treatment, and sample rule and audits the control-set search dimension. Expanding all SCE dimensions requires a common protected prediction target rather than silently comparing different outcomes.', 'execution_mode': 'audit'}

def evaluate(records, *, baseline=None, budget=None):
    return evaluate_spec_product(PRODUCT_SPEC, records, baseline=baseline, budget=budget)
