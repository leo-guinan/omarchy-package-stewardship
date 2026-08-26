import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from omarchy_stewardship.promotion import Artifact, promote_edge_to_stable, rollback_to_previous_stable

previous = Artifact("demo-package", "1.0", "x86_64", "sha256:old")
candidate = Artifact("demo-package", "1.1", "x86_64", "sha256:new")
receipt = promote_edge_to_stable(
    candidate=candidate,
    previous_stable=previous,
    evidence={"artifact_digest": "sha256:new", "tests_passed": True},
    actor="demo-maintainer",
    observed_at="2026-08-26T12:00:00Z",
)
rollback = rollback_to_previous_stable(receipt, actor="demo-maintainer", observed_at="2026-08-26T12:05:00Z")
print(f"promoted={receipt.promoted_artifact_digest} rollback_target={rollback.target_digest} receipt={receipt.receipt_id}")
