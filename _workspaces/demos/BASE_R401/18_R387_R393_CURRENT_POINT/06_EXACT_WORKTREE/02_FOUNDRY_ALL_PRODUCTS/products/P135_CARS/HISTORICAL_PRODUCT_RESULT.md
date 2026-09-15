# P135 CARS — Certificate-Aware Resolution Sensing

Parents: TSRC -> ACRA.

TSRC first certifies which features can be deleted inside the declared action shell. CARS then gives deleted features zero sensing consequence and lets ACRA spend a shared resolution budget only where retained features can still change the protected score.

Benchmark: TSRC deletes `secondary` and high-cost `nuisance`, retaining only `critical`. Under a budget that permits exactly one fine-resolution slot, ACRA assigns `critical -> fine` and both certified-deletable features -> coarse. Total decision loss is 0.0005.

Claim boundary: zero sensing consequence is valid only inside the same TSRC deletion shell and protected action target. It is not a statement that the deleted feature is scientifically irrelevant.

Status: WORKING_COMPOSITION; 6/6 tests.
