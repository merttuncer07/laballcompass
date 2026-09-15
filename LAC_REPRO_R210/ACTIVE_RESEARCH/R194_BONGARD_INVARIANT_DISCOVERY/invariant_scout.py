from __future__ import annotations

import itertools
from dataclasses import dataclass

import numpy as np


def affine_quotient(z: np.ndarray) -> np.ndarray:
    """Remove per-scene translation and positive scale nuisance."""
    z = np.asarray(z, dtype=float)
    diff = z[:, :-1] - z[:, [-1]]
    scale = np.sqrt(np.mean(diff**2, axis=1, keepdims=True)) + 1e-12
    return diff / scale


def lifted_library(z: np.ndarray) -> tuple[np.ndarray, list[str]]:
    d = affine_quotient(z)
    cols = []
    names = []
    for j in range(d.shape[1]):
        cols.append(d[:, j])
        names.append(f"d{j}")
    for j in range(d.shape[1]):
        cols.append(d[:, j] ** 2)
        names.append(f"d{j}^2")
    for j in range(d.shape[1]):
        for k in range(j + 1, d.shape[1]):
            cols.append(d[:, j] * d[:, k])
            names.append(f"d{j}*d{k}")
    return np.column_stack(cols), names


def residual_score(features: np.ndarray, coefficients: np.ndarray) -> np.ndarray:
    numerator = np.abs(features @ coefficients)
    denominator = np.linalg.norm(features, axis=1) * np.linalg.norm(coefficients) + 1e-12
    return numerator / denominator


def balanced_accuracy(pred: np.ndarray, y: np.ndarray) -> float:
    pos = y == 1
    neg = ~pos
    return float(0.5 * (np.mean(pred[pos] == 1) + np.mean(pred[neg] == 0)))


def select_threshold(scores: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    values = np.unique(np.concatenate([[0.0], scores, [scores.max() + 1e-12]]))
    thresholds = (values[:-1] + values[1:]) / 2.0
    best = (-1.0, 0.0)
    for threshold in thresholds:
        acc = balanced_accuracy((scores <= threshold).astype(np.int8), y)
        if acc > best[0]:
            best = (acc, float(threshold))
    return best[1], best[0]


@dataclass
class SparseInvariantScout:
    max_terms: int = 4
    min_validation_accuracy: float = 0.74
    min_separation_ratio: float = 2.0
    min_stability_cosine: float = 0.94
    max_audit_positive_residual: float = 0.030
    discovery_fraction: float = 0.55

    support_: tuple[int, ...] | None = None
    coefficients_: np.ndarray | None = None
    threshold_: float | None = None
    feature_names_: list[str] | None = None
    validation_accuracy_: float | None = None
    separation_ratio_: float | None = None
    stability_cosine_: float | None = None
    audit_positive_residual_: float | None = None
    abstained_: bool = True

    def fit(self, z: np.ndarray, y: np.ndarray):
        z = np.asarray(z, dtype=float)
        y = np.asarray(y, dtype=np.int8)
        features, names = lifted_library(z)
        pos = np.flatnonzero(y == 1)
        neg = np.flatnonzero(y == 0)
        if len(pos) < self.max_terms + 3 or len(neg) < 5:
            raise ValueError("more positive and negative examples are required")
        n_discovery = max(self.max_terms + 1, int(len(pos) * self.discovery_fraction))
        discovery = pos[:n_discovery]
        remaining_pos = pos[n_discovery:]
        pos_cut = max(2, len(remaining_pos) // 2)
        neg_cut = max(3, len(neg) // 2)
        selection = np.concatenate([remaining_pos[:pos_cut], neg[:neg_cut]])
        audit = np.concatenate([remaining_pos[pos_cut:], neg[neg_cut:]])
        if np.sum(y[audit] == 1) < 2 or np.sum(y[audit] == 0) < 3:
            raise ValueError("not enough examples for untouched relation audit")

        best_key = None
        best = None
        degrees = np.array([1 if "^" not in name and "*" not in name else 2 for name in names])
        for size in range(2, self.max_terms + 1):
            for support in itertools.combinations(range(features.shape[1]), size):
                fd = features[np.ix_(discovery, support)]
                _, singular, vh = np.linalg.svd(fd, full_matrices=False)
                coeff = vh[-1]
                fs = features[np.ix_(selection, support)]
                scores = residual_score(fs, coeff)
                threshold, accuracy = select_threshold(scores, y[selection])
                pos_scores = scores[y[selection] == 1]
                neg_scores = scores[y[selection] == 0]
                positive_residual = float(np.median(pos_scores))
                separation = float(
                    np.median(neg_scores) / (np.median(pos_scores) + 1e-9)
                )
                null_ratio = float(singular[-1] / (singular[0] + 1e-12))
                # Accuracy dominates; then require a large residual gap, a simpler
                # relation and a cleaner positive nullspace.
                max_degree = int(degrees[list(support)].max())
                # Prefer a minimal law over a higher-degree multiple of that law.
                # The penalties are smaller than one held-out positive mistake,
                # so accuracy can still overturn simplicity when the evidence is real.
                utility = (
                    accuracy
                    + 0.045 * min(math_log10(separation), 4.0)
                    + 0.045 * min(max(-math_log10(positive_residual), 0.0), 4.0)
                    - 0.035 * (max_degree - 1)
                    - 0.012 * (size - 2)
                )
                key = (
                    positive_residual <= 0.06,
                    utility,
                    accuracy,
                    min(math_log10(separation), 6.0),
                    -size,
                    -null_ratio,
                )
                if best_key is None or key > best_key:
                    best_key = key
                    best = (support, coeff, threshold, accuracy, separation)

        support, coefficients, threshold, _, _ = best
        # A larger candidate can win because it contains the true sparse relation
        # plus numerically tiny nuisance terms. Remove only coefficients below 5%
        # of the dominant term, refit on discovery, and re-check selection.
        keep = np.abs(coefficients) >= 0.05 * np.max(np.abs(coefficients))
        if 2 <= int(keep.sum()) < len(support):
            support = tuple(np.asarray(support)[keep].tolist())
            fp = features[np.ix_(discovery, support)]
            _, _, vh = np.linalg.svd(fp, full_matrices=False)
            coefficients = vh[-1]
            selection_scores = residual_score(features[np.ix_(selection, support)], coefficients)
            threshold, _ = select_threshold(selection_scores, y[selection])

        # The audit set did not choose the relation or its threshold. It is the
        # multiple-hypothesis defense against finding a fake vanishing equation.
        audit_scores = residual_score(features[np.ix_(audit, support)], coefficients)
        audit_pred = (audit_scores <= threshold).astype(np.int8)
        validation_accuracy = balanced_accuracy(audit_pred, y[audit])
        audit_pos = audit_scores[y[audit] == 1]
        audit_neg = audit_scores[y[audit] == 0]
        audit_positive_residual = float(np.median(audit_pos))
        separation = float(np.median(audit_neg) / (np.median(audit_pos) + 1e-9))

        # A genuine invariant should yield the same coefficient direction in a
        # positive subset that did not fit the candidate.
        confirm = features[np.ix_(remaining_pos, support)]
        _, _, vh_confirm = np.linalg.svd(confirm, full_matrices=False)
        confirm_coefficients = vh_confirm[-1]
        stability = float(
            abs(np.dot(coefficients, confirm_coefficients))
            / (np.linalg.norm(coefficients) * np.linalg.norm(confirm_coefficients) + 1e-12)
        )

        # Once the claim passes untouched audit, use all positives for the final
        # deployable coefficient estimate and all training rows for calibration.
        fp = features[np.ix_(pos, support)]
        _, _, vh = np.linalg.svd(fp, full_matrices=False)
        coefficients = vh[-1]
        scores = residual_score(features[:, support], coefficients)
        threshold, _ = select_threshold(scores, y)

        self.support_ = tuple(int(i) for i in support)
        self.coefficients_ = coefficients
        self.threshold_ = threshold
        self.feature_names_ = names
        self.validation_accuracy_ = float(validation_accuracy)
        self.separation_ratio_ = float(separation)
        self.stability_cosine_ = stability
        self.audit_positive_residual_ = audit_positive_residual
        self.abstained_ = not (
            validation_accuracy >= self.min_validation_accuracy
            and separation >= self.min_separation_ratio
            and stability >= self.min_stability_cosine
            and audit_positive_residual <= self.max_audit_positive_residual
        )
        return self

    def relation(self) -> list[tuple[str, float]] | None:
        if self.support_ is None or self.abstained_:
            return None
        coeff = self.coefficients_ / (np.max(np.abs(self.coefficients_)) + 1e-12)
        return [(self.feature_names_[i], float(c)) for i, c in zip(self.support_, coeff)]

    def predict(self, z: np.ndarray) -> np.ndarray:
        if self.support_ is None:
            raise RuntimeError("fit must be called first")
        if self.abstained_:
            return np.full(len(z), -1, dtype=np.int8)
        features, _ = lifted_library(z)
        scores = residual_score(features[:, self.support_], self.coefficients_)
        return (scores <= self.threshold_).astype(np.int8)

    def diagnostics(self) -> dict:
        return {
            "abstained": self.abstained_,
            "validation_accuracy": self.validation_accuracy_,
            "separation_ratio": self.separation_ratio_,
            "stability_cosine": self.stability_cosine_,
            "audit_positive_median_residual": self.audit_positive_residual_,
            "relation": self.relation(),
        }


def math_log10(value: float) -> float:
    return float(np.log10(max(value, 1e-12)))
