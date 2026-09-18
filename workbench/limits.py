"""Bounded budgets shared by the workbook review engines.

These are review-engine budgets, not claims about Excel's maximum size. The
per-file and collection budgets are separate so a pair of moderately sized,
sparse workbooks can be compared without making one oversized input
acceptable by accident.
"""

POPULATED_CELLS_PER_WORKBOOK = 150_000
POPULATED_CELLS_PER_COLLECTION = 300_000

# A sparse worksheet can have a large bounding box with relatively few cells.
# Keep a guard for genuinely wide sheets, but do not use the old 100,000-cell
# box as a proxy for populated data.
WORKSHEET_BOUNDING_CELLS = 2_000_000

DETAIL_POSITIONS = 100_000
DETAIL_BLOCKS = 200

# Static lineage is more expensive than a coordinate/value comparison. It may
# fail closed while the content report remains useful.
LINEAGE_NODES = 30_000
LINEAGE_RULE_INPUTS = 250_000
