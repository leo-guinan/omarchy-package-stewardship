import hashlib
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from omarchy_stewardship.promotion import (
    Artifact,
    artifact_from_file,
    promote_edge_to_stable,
    rollback_to_previous_stable,
)

with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / "demo-package.pkg.tar.zst"
    path.write_bytes(b"demo package artifact bytes")
    candidate = artifact_from_file(
        name="demo-package", version="1.1", architecture="x86_64", path=path
    )
    previous = Artifact("demo-package", "1.0", "x86_64", "sha256:old")
    evidence = {
        "artifact_digest": candidate.digest,
        "architecture": candidate.architecture,
        "build_id": "build-demo-001",
        "signature_valid": True,
        "tests_passed": True,
    }
    receipt = promote_edge_to_stable(
        candidate=candidate,
        previous_stable=previous,
        evidence=evidence,
        actor="demo-maintainer",
        observed_at="2026-08-26T12:00:00Z",
    )
    rollback = rollback_to_previous_stable(
        receipt, actor="demo-maintainer", observed_at="2026-08-26T12:05:00Z"
    )
    expected = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
    assert candidate.digest == expected
    assert rollback.target_digest == "sha256:old"
    print(
        f"hashed={candidate.digest} promoted={receipt.promoted_artifact_digest} "
        f"rollback_target={rollback.target_digest} receipt={receipt.receipt_id}"
    )
