"""Deterministic promotion and rollback receipts."""

from dataclasses import dataclass
import hashlib
import json
from collections.abc import Mapping


class EvidenceMismatch(ValueError):
    """Raised when promotion evidence does not describe the candidate."""


@dataclass(frozen=True)
class Artifact:
    name: str
    version: str
    architecture: str
    digest: str


@dataclass(frozen=True)
class PromotionReceipt:
    receipt_id: str
    package_name: str
    promoted_artifact_digest: str
    rollback_target_digest: str | None
    from_channel: str
    to_channel: str
    actor: str
    observed_at: str


@dataclass(frozen=True)
class RollbackReceipt:
    receipt_id: str
    source_promotion_receipt: str
    target_digest: str
    actor: str
    observed_at: str


def _receipt_id(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return "receipt:" + hashlib.sha256(encoded).hexdigest()


def promote_edge_to_stable(
    *,
    candidate: Artifact,
    previous_stable: Artifact | None,
    evidence: dict[str, object],
    actor: str,
    observed_at: str,
) -> PromotionReceipt:
    """Promote an edge artifact only when its evidence matches exactly."""
    if evidence.get("artifact_digest") != candidate.digest:
        raise EvidenceMismatch("artifact digest does not match candidate")
    if evidence.get("tests_passed") is not True:
        raise EvidenceMismatch("tests evidence is not passing")
    if not actor or not observed_at:
        raise ValueError("actor and observed_at are required")

    rollback_target = previous_stable.digest if previous_stable else None
    fields = {
        "package_name": candidate.name,
        "promoted_artifact_digest": candidate.digest,
        "rollback_target_digest": rollback_target,
        "from_channel": "edge",
        "to_channel": "stable",
        "actor": actor,
        "observed_at": observed_at,
    }
    return PromotionReceipt(receipt_id=_receipt_id(fields), **fields)


def rollback_to_previous_stable(
    receipt: PromotionReceipt, *, actor: str, observed_at: str
) -> RollbackReceipt:
    """Create a rollback receipt from a prior promotion's retained target."""
    if receipt.rollback_target_digest is None:
        raise ValueError("promotion has no rollback target")
    if not actor or not observed_at:
        raise ValueError("actor and observed_at are required")

    fields = {
        "source_promotion_receipt": receipt.receipt_id,
        "target_digest": receipt.rollback_target_digest,
        "actor": actor,
        "observed_at": observed_at,
    }
    return RollbackReceipt(receipt_id=_receipt_id(fields), **fields)
