import pytest

from omarchy_stewardship.promotion import (
    Artifact,
    EvidenceMismatch,
    PromotionReceipt,
    promote_edge_to_stable,
    rollback_to_previous_stable,
)


def artifact(digest: str, version: str) -> Artifact:
    return Artifact(
        name="demo-package",
        version=version,
        architecture="aarch64",
        digest=digest,
    )


def test_promotion_preserves_exact_artifact_and_rollback_target():
    previous = artifact("sha256:old", "1.0")
    candidate = artifact("sha256:new", "1.1")

    receipt = promote_edge_to_stable(
        candidate=candidate,
        previous_stable=previous,
        evidence={"artifact_digest": "sha256:new", "tests_passed": True},
        actor="leo",
        observed_at="2026-08-26T12:00:00Z",
    )

    assert isinstance(receipt, PromotionReceipt)
    assert receipt.promoted_artifact_digest == "sha256:new"
    assert receipt.rollback_target_digest == "sha256:old"
    assert receipt.from_channel == "edge"
    assert receipt.to_channel == "stable"

    rollback = rollback_to_previous_stable(receipt, actor="leo", observed_at="2026-08-26T12:05:00Z")
    assert rollback.target_digest == "sha256:old"
    assert rollback.source_promotion_receipt == receipt.receipt_id


def test_promotion_rejects_evidence_for_a_different_artifact():
    with pytest.raises(EvidenceMismatch, match="artifact digest"):
        promote_edge_to_stable(
            candidate=artifact("sha256:new", "1.1"),
            previous_stable=artifact("sha256:old", "1.0"),
            evidence={"artifact_digest": "sha256:other", "tests_passed": True},
            actor="leo",
            observed_at="2026-08-26T12:00:00Z",
        )


def test_promotion_rejects_failed_tests():
    with pytest.raises(EvidenceMismatch, match="tests"):
        promote_edge_to_stable(
            candidate=artifact("sha256:new", "1.1"),
            previous_stable=None,
            evidence={"artifact_digest": "sha256:new", "tests_passed": False},
            actor="leo",
            observed_at="2026-08-26T12:00:00Z",
        )


def test_identical_promotion_inputs_produce_identical_receipt_id():
    kwargs = {
        "candidate": artifact("sha256:new", "1.1"),
        "previous_stable": artifact("sha256:old", "1.0"),
        "evidence": {"artifact_digest": "sha256:new", "tests_passed": True},
        "actor": "leo",
        "observed_at": "2026-08-26T12:00:00Z",
    }

    first = promote_edge_to_stable(**kwargs)
    second = promote_edge_to_stable(**kwargs)

    assert first.receipt_id == second.receipt_id
