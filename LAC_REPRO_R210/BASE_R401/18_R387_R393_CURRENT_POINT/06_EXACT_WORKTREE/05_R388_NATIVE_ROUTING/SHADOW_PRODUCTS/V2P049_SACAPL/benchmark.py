import json
from test_sacapl import case

result = case(False)
out = {
    "mechanism_removing_comparator": "same CAPL linear-softmax action map, constraints, optimizer, seed, returns and transaction costs, but the policy risk objective uses the unstructured raw sample covariance instead of SACPS support-aware covariance",
    "evidence_boundary": "deterministic synthetic sparse-covariance shell with declared correct support and deliberately finite-sample off-support nuisance covariance; establishes the composition mechanism and a working region, not empirical market alpha or a universal portfolio theorem",
    "working_region": "declared covariance support is materially informative and the raw risk sample contains off-support estimation error large enough to change policy selection",
    "collapse_region": "with fully dense declared support and shrinkage fixed at zero, SACPS covariance equals raw covariance and the candidate collapses exactly to the removal control",
    "result": result,
}
with open("BENCHMARK_RESULT.json", "w", encoding="utf-8") as handle:
    json.dump(out, handle, indent=2)
print(json.dumps(out, indent=2))
