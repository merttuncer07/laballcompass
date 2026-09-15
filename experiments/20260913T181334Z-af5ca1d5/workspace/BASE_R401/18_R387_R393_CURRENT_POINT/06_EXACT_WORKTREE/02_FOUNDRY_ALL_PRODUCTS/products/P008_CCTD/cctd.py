"""Confidence-Calibrated Trigger Designer (CCTD) v0.3.

Composition contract:
1. CWC calibrates a prediction-interval multiplier on a historical calibration segment.
2. The calibrated multiplier creates center/lower/upper signal views on a separate design segment.
3. DTTC selects the signal view and threshold that minimize declared operational trigger loss.
4. A frozen deployment object applies the selected view/threshold to untouched data.

The interval bounds are candidate trigger signals, not event labels or causal claims.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

import numpy as np

if __package__:
    from .parents.acsa import audit_adaptive_selection
else:
    from parents.acsa import audit_adaptive_selection
if __package__:
    from .parents.cwc import CalibrationWidthController
else:
    from parents.cwc import CalibrationWidthController
if __package__:
    from .parents.dttc import DecisionTargetedTriggerDesigner, TriggerCandidate
else:
    from parents.dttc import DecisionTargetedTriggerDesigner, TriggerCandidate


def _vector(values: Sequence[float], name: str) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    if arr.ndim != 1 or arr.size == 0 or not np.all(np.isfinite(arr)):
        raise ValueError(f"{name} must be a non-empty finite vector")
    return arr


@dataclass(frozen=True)
class TriggerDeployment:
    signal_view: str
    threshold: float
    calibrated_multiplier: float
    target_coverage: float
    objective_on_design: float
    false_negative_cost: float
    false_positive_cost: float
    fixed_policy_cost: float = 0.0

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def signal(self, center: Sequence[float], base_scale: Sequence[float]) -> np.ndarray:
        center_arr = _vector(center, "center")
        scale_arr = _vector(base_scale, "base_scale")
        if len(center_arr) != len(scale_arr):
            raise ValueError("center and base_scale lengths must match")
        if np.any(scale_arr <= 0):
            raise ValueError("base_scale must be positive")
        if self.signal_view == "center":
            return center_arr
        if self.signal_view == "lower":
            return center_arr - self.calibrated_multiplier * scale_arr
        if self.signal_view == "upper":
            return center_arr + self.calibrated_multiplier * scale_arr
        raise ValueError(f"Unknown signal_view: {self.signal_view}")

    def predict(self, center: Sequence[float], base_scale: Sequence[float]) -> np.ndarray:
        return self.signal(center, base_scale) >= self.threshold


class ConfidenceCalibratedTriggerDesigner:
    def __init__(
        self,
        *,
        target_coverage: float = 0.90,
        false_negative_cost: float = 1.0,
        false_positive_cost: float = 1.0,
        threshold_grid_size: int = 201,
    ) -> None:
        if not 0.0 < target_coverage < 1.0:
            raise ValueError("target_coverage must be in (0,1)")
        self.target_coverage = float(target_coverage)
        self.fn_cost = float(false_negative_cost)
        self.fp_cost = float(false_positive_cost)
        self.threshold_grid_size = int(threshold_grid_size)
        self.calibrated_multiplier: float | None = None

    def calibrate(
        self,
        outcomes: Sequence[float],
        centers: Sequence[float],
        base_scales: Sequence[float],
        *,
        initial_multiplier: float = 1.645,
    ) -> dict[str, float]:
        y = _vector(outcomes, "outcomes")
        c = _vector(centers, "centers")
        s = _vector(base_scales, "base_scales")
        if not (len(y) == len(c) == len(s)):
            raise ValueError("calibration arrays must have matching lengths")
        if np.any(s <= 0):
            raise ValueError("base_scales must be positive")

        controller = CalibrationWidthController(
            target_coverage=self.target_coverage,
            initial_multiplier=initial_multiplier,
        )
        hits = []
        for outcome, center, scale in zip(y, c, s):
            obs = controller.observe(float(outcome), float(center), float(scale))
            hits.append(obs.covered)
        self.calibrated_multiplier = controller.multiplier
        return {
            "calibrated_multiplier": float(self.calibrated_multiplier),
            "calibration_coverage": float(np.mean(hits)),
            "target_coverage": self.target_coverage,
        }

    def build_signal_views(
        self, centers: Sequence[float], base_scales: Sequence[float]
    ) -> dict[str, np.ndarray]:
        if self.calibrated_multiplier is None:
            raise RuntimeError("calibrate must be called before signal construction")
        c = _vector(centers, "centers")
        s = _vector(base_scales, "base_scales")
        if len(c) != len(s):
            raise ValueError("centers and base_scales lengths must match")
        if np.any(s <= 0):
            raise ValueError("base_scales must be positive")
        k = self.calibrated_multiplier
        return {"center": c, "lower": c - k * s, "upper": c + k * s}

    def design(
        self,
        centers: Sequence[float],
        base_scales: Sequence[float],
        protected_event: Sequence[bool],
        loss: Sequence[float],
        *,
        candidate_costs: Mapping[str, float] | None = None,
        manipulation_exposure: Mapping[str, float] | None = None,
    ) -> dict[str, Any]:
        views = self.build_signal_views(centers, base_scales)
        event = np.asarray(protected_event, dtype=bool)
        losses = _vector(loss, "loss")
        if len(event) != len(losses) or len(event) != len(next(iter(views.values()))):
            raise ValueError("design arrays must have matching lengths")
        costs = dict(candidate_costs or {})
        manipulation = dict(manipulation_exposure or {})
        candidates = [
            TriggerCandidate(
                name=name,
                verification_cost=float(costs.get(name, 0.0)),
                manipulation_exposure=float(manipulation.get(name, 0.0)),
            )
            for name in ("center", "lower", "upper")
        ]
        designer = DecisionTargetedTriggerDesigner(
            false_negative_cost=self.fn_cost,
            false_positive_cost=self.fp_cost,
            threshold_grid_size=self.threshold_grid_size,
        )
        result = designer.design(candidates, views, event, losses)
        selected = result["selected"]
        deployment = TriggerDeployment(
            signal_view=str(selected["candidate"]),
            threshold=float(selected["threshold"]),
            calibrated_multiplier=float(self.calibrated_multiplier),
            target_coverage=self.target_coverage,
            objective_on_design=float(selected["objective"]),
            false_negative_cost=self.fn_cost,
            false_positive_cost=self.fp_cost,
            fixed_policy_cost=float(selected["verification_cost"] + selected["manipulation_cost"]),
        )
        return {
            "deployment": deployment,
            "design": result,
            "calibrated_multiplier": float(self.calibrated_multiplier),
        }


    def _deployments_from_design(self, design_result: Mapping[str, Any]) -> dict[str, TriggerDeployment]:
        if self.calibrated_multiplier is None:
            raise RuntimeError("calibrate must be called before protected audit")
        policies: dict[str, TriggerDeployment] = {}
        for row in design_result["ranking"]:
            name = str(row["candidate"])
            policies[name] = TriggerDeployment(
                signal_view=name,
                threshold=float(row["threshold"]),
                calibrated_multiplier=float(self.calibrated_multiplier),
                target_coverage=self.target_coverage,
                objective_on_design=float(row["objective"]),
                false_negative_cost=self.fn_cost,
                false_positive_cost=self.fp_cost,
                fixed_policy_cost=float(row["verification_cost"] + row["manipulation_cost"]),
            )
        return policies

    @staticmethod
    def _policy_loss_matrix(
        policies: Mapping[str, TriggerDeployment],
        centers: Sequence[float],
        base_scales: Sequence[float],
        protected_event: Sequence[bool],
    ) -> tuple[tuple[str, ...], np.ndarray]:
        event = np.asarray(protected_event, dtype=bool)
        # Preserve DTTC ranking/insertion order so exact objective ties use the
        # same deterministic tie-break as the design stage.
        names = tuple(policies)
        if event.ndim != 1 or event.size == 0:
            raise ValueError("protected_event must be a non-empty vector")
        losses = np.empty((len(event), len(names)), dtype=float)
        for j, name in enumerate(names):
            policy = policies[name]
            pred = policy.predict(centers, base_scales)
            if len(pred) != len(event):
                raise ValueError("policy inputs and event lengths must match")
            losses[:, j] = (
                policy.false_negative_cost * (event & ~pred).astype(float)
                + policy.false_positive_cost * (~event & pred).astype(float)
                + policy.fixed_policy_cost
            )
        return names, losses

    def design_with_protected_audit(
        self,
        *,
        design_centers: Sequence[float],
        design_base_scales: Sequence[float],
        design_event: Sequence[bool],
        design_loss: Sequence[float],
        protected_centers: Sequence[float],
        protected_base_scales: Sequence[float],
        protected_event: Sequence[bool],
        candidate_costs: Mapping[str, float] | None = None,
        manipulation_exposure: Mapping[str, float] | None = None,
        bootstrap_samples: int = 500,
        random_seed: int = 0,
        material_regret: float = 0.0,
        protected_promotion_z: float = 1.96,
        incumbent_signal_view: str = "center",
    ) -> dict[str, Any]:
        """Design candidates, then require protected evidence before promotion.

        `center` is the default incumbent/no-op policy.  A lower/upper confidence
        view is promoted only when its *paired* protected-sample improvement over
        the incumbent exceeds both the requested material margin and a z-scaled
        standard-error guard.  The protected sample therefore acts as a promotion
        gate, not as the final performance report; any promoted policy still needs
        a separate fresh-final evaluation.
        """
        if protected_promotion_z < 0:
            raise ValueError("protected_promotion_z must be nonnegative")
        if material_regret < 0:
            raise ValueError("material_regret must be nonnegative")

        designed = self.design(
            design_centers,
            design_base_scales,
            design_event,
            design_loss,
            candidate_costs=candidate_costs,
            manipulation_exposure=manipulation_exposure,
        )
        policies = self._deployments_from_design(designed["design"])
        if incumbent_signal_view not in policies:
            raise ValueError("incumbent_signal_view must name a designed policy")

        names, selection_losses = self._policy_loss_matrix(
            policies, design_centers, design_base_scales, design_event
        )
        holdout_names, holdout_losses = self._policy_loss_matrix(
            policies, protected_centers, protected_base_scales, protected_event
        )
        if names != holdout_names:
            raise RuntimeError("policy ordering changed")

        audit = audit_adaptive_selection(
            selection_losses,
            holdout_losses,
            candidate_names=names,
            bootstrap_samples=bootstrap_samples,
            random_seed=random_seed,
            material_regret=material_regret,
        )

        incumbent_idx = names.index(incumbent_signal_view)
        holdout_means = holdout_losses.mean(axis=0)
        protected_best_idx = int(np.argmin(holdout_means))
        protected_best_name = names[protected_best_idx]
        incumbent_mean = float(holdout_means[incumbent_idx])
        protected_best_mean = float(holdout_means[protected_best_idx])
        protected_improvement = incumbent_mean - protected_best_mean

        if protected_best_idx == incumbent_idx:
            paired_se = 0.0
        else:
            paired_advantage = (
                holdout_losses[:, incumbent_idx] - holdout_losses[:, protected_best_idx]
            )
            paired_se = float(
                np.std(paired_advantage, ddof=1) / np.sqrt(len(paired_advantage))
            )
        promotion_radius = float(protected_promotion_z * paired_se)
        promotion_threshold = float(material_regret + promotion_radius)
        promoted = bool(
            protected_best_idx != incumbent_idx
            and protected_improvement > promotion_threshold
        )
        stable_name = protected_best_name if promoted else incumbent_signal_view

        return {
            "design_selected": designed["deployment"],
            "policies": policies,
            "audit": audit,
            "stable_deployment": policies[stable_name],
            "promotion_gate": {
                "incumbent_candidate": incumbent_signal_view,
                "protected_best_candidate": protected_best_name,
                "incumbent_protected_mean_loss": incumbent_mean,
                "protected_best_mean_loss": protected_best_mean,
                "protected_improvement_vs_incumbent": float(protected_improvement),
                "paired_standard_error": paired_se,
                "protected_promotion_z": float(protected_promotion_z),
                "promotion_radius": promotion_radius,
                "material_margin": float(material_regret),
                "promotion_threshold": promotion_threshold,
                "promoted": promoted,
            },
            "status": (
                "PROTECTED_PROMOTION_REQUIRES_FRESH_FINAL_VALIDATION"
                if promoted
                else "INCUMBENT_RETAINED_AFTER_PROTECTED_GATE"
            ),
        }

    def center_only_design(
        self,
        centers: Sequence[float],
        protected_event: Sequence[bool],
        loss: Sequence[float],
    ) -> TriggerDeployment:
        if self.calibrated_multiplier is None:
            raise RuntimeError("calibrate must be called before design")
        c = _vector(centers, "centers")
        event = np.asarray(protected_event, dtype=bool)
        losses = _vector(loss, "loss")
        designer = DecisionTargetedTriggerDesigner(
            false_negative_cost=self.fn_cost,
            false_positive_cost=self.fp_cost,
            threshold_grid_size=self.threshold_grid_size,
        )
        result = designer.fit_candidate(
            TriggerCandidate("center"), c, event, losses
        )
        return TriggerDeployment(
            signal_view="center",
            threshold=result.threshold,
            calibrated_multiplier=float(self.calibrated_multiplier),
            target_coverage=self.target_coverage,
            objective_on_design=result.objective,
            false_negative_cost=self.fn_cost,
            false_positive_cost=self.fp_cost,
        )


def evaluate_deployment(
    deployment: TriggerDeployment,
    centers: Sequence[float],
    base_scales: Sequence[float],
    protected_event: Sequence[bool],
) -> dict[str, float]:
    pred = deployment.predict(centers, base_scales)
    event = np.asarray(protected_event, dtype=bool)
    if len(pred) != len(event):
        raise ValueError("prediction and event lengths must match")
    fn = float(np.mean(event & ~pred))
    fp = float(np.mean(~event & pred))
    objective = (
        deployment.false_negative_cost * fn
        + deployment.false_positive_cost * fp
        + deployment.fixed_policy_cost
    )
    return {
        "objective": objective,
        "fixed_policy_cost": float(deployment.fixed_policy_cost),
        "false_negative_rate_population": fn,
        "false_positive_rate_population": fp,
        "activation_rate": float(np.mean(pred)),
        "event_rate": float(np.mean(event)),
    }
