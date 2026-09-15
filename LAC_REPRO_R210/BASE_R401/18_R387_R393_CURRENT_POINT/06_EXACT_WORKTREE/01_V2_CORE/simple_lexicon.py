"""Simple canonical lexicon for LabAllCompass primitives.

Canonical mechanism identity is deliberately domain-neutral:
    primitive + constraint shell

Source/domain labels remain provenance/search aliases only. They are not part of
canonical mechanism identity and must not silently change deduplication.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping
import hashlib, json, re

MODEL_VERSION = "LAB_SIMPLE_LEXICON_R12_V1"
WS = re.compile(r"\s+")


def _clean(x: object) -> str:
    return WS.sub(" ", str(x or "").strip())


def canonical_mechanism_text(row: Mapping[str, object]) -> str:
    primitive = _clean(row.get("primitive"))
    shell = _clean(row.get("constraint_shell"))
    if not primitive:
        raise ValueError("primitive text is required")
    return primitive if not shell else f"{primitive} | constraint: {shell}"


def canonical_mechanism_id(row: Mapping[str, object]) -> str:
    payload = {
        "model_version": MODEL_VERSION,
        "primitive": _clean(row.get("primitive")),
        "constraint_shell": _clean(row.get("constraint_shell")),
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def provenance_aliases(row: Mapping[str, object]) -> tuple[str, ...]:
    vals = [_clean(row.get("source_concept")), _clean(row.get("domain"))]
    return tuple(v for v in vals if v)


@dataclass(frozen=True)
class CanonicalPrimitive:
    primitive_id: str
    canonical_text: str
    canonical_fingerprint: str
    source_concept: str
    domain: str
    aliases: tuple[str, ...]

    @classmethod
    def from_row(cls, row: Mapping[str, object]) -> "CanonicalPrimitive":
        return cls(
            primitive_id=_clean(row.get("id")),
            canonical_text=canonical_mechanism_text(row),
            canonical_fingerprint=canonical_mechanism_id(row),
            source_concept=_clean(row.get("source_concept")),
            domain=_clean(row.get("domain")),
            aliases=provenance_aliases(row),
        )
