# P103 CFAI implementation status

The historical description survives, but its original source and tests do not. They have not been recovered.

On 2026-09-14, the generic score-only `spec_runtime` adapter was replaced by a **new native implementation** of the described HFAD → BICC → ACRA composition. It accepts an oriented graph and flow scenarios, measures coordinate replacement effects on Hodge cycle-space energy, and allocates resolution using an explicit additive influence score and budget.

Implementation identity: `native_reimplementation_20260914`. It does not inherit historical benchmark results or establish fraud detection, calibrated audit risk, or user benefit. In particular, Hodge's signed cycle-space projection is not proof of a directed circular payment.

Previous executable files are preserved under the lab's `restoration/20260914-product-repairs/before/P103_CFAI/`. See the current `PRODUCT_REPAIRS.md` at the lab root for tested behavior and limitations.
