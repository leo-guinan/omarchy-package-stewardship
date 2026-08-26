import hashlib

import pytest

from omarchy_stewardship.promotion import (
    Artifact,
    EvidenceMismatch,
    PromotionReceipt,
    artifact_from_file,
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


def evidence(digest: str, architecture: str = "aarch64") -> dict[str, object]:
    return {
        "artifact_digest": digest,
        "architecture": architecture,
        "build_id": "build-001",
        "signature_valid": True,
        "tests_passed": True,
    }


def test_promotion_preserves_exact_artifact_and_rollback_target():
    previous = artifact("sha256:old", "1.0")
    candidate = artifact("sha256:new", "1.1")

    receipt = promote_edge_to_stable(
        candidate=candidate,
        previous_stable=previous,
        evidence=evidence("sha256:new"),
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
            evidence=evidence("sha256:other"),
            actor="leo",
            observed_at="2026-08-26T12:00:00Z",
        )


def test_promotion_rejects_failed_tests():
    bad = evidence("sha256:new")
    bad["tests_passed"] = False
    with pytest.raises(EvidenceMismatch, match="tests"):
        promote_edge_to_stable(
            candidate=artifact("sha256:new", "1.1"),
            previous_stable=None,
            evidence=bad,
            actor="leo",
            observed_at="2026-08-26T12:00:00Z",
        )


def test_identical_promotion_inputs_produce_identical_receipt_id():
    kwargs = {
        "candidate": artifact("sha256:new", "1.1"),
        "previous_stable": artifact("sha256:old", "1.0"),
        "evidence": evidence("sha256:new"),
        "actor": "leo",
        "observed_at": "2026-08-26T12:00:00Z",
    }

    first = promote_edge_to_stable(**kwargs)
    second = promote_edge_to_stable(**kwargs)

    assert first.receipt_id == second.receipt_id


def test_artifact_digest_is_computed_from_file_bytes(tmp_path):
    package = tmp_path / "demo-package.pkg.tar.zst"
    package.write_bytes(b"real artifact bytes\x00\x01")

    result = artifact_from_file(
        name="demo-package",
        version="1.1",
        architecture="aarch64",
        path=package,
    )

    expected = "sha256:" + hashlib.sha256(package.read_bytes()).hexdigest()
    assert result.digest == expected
    assert result.source_path == str(package)


def test_promotion_rejects_missing_build_signature_or_architecture_evidence():
    for key in ("build_id", "signature_valid", "architecture"):
        incomplete = evidence("sha256:new")
        del incomplete[key]
        with pytest.raises(EvidenceMismatch, match="evidence"):
            promote_edge_to_stable(
                candidate=artifact("sha256:new", "1.1"),
                previous_stable=None,
                evidence=incomplete,
                actor="leo",
                observed_at="2026-08-26T12:00:00Z",
            )
