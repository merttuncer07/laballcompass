import json

from fcms import synthesize_compatible_microstructure


phases = [
    [[1, 0], [0, 1]],
    [[-1, 0], [0, 1]],
    [[1, 0], [0, -1]],
    [[-1, 0], [0, -1]],
]
result = synthesize_compatible_microstructure(
    phases,
    [[0, 0], [0, 0]],
    phase_names=["A++", "A-+", "A+-", "A--"],
    maximum_lamination_depth=3,
    specimen_thickness=1.0,
    minimum_fabrication_feature=.2,
)
summary = result.to_dict(); summary.pop("tree")
print(json.dumps(summary, indent=2))
