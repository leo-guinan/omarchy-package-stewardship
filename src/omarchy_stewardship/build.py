"""Controlled boundary for building one Arch package."""

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import shutil
import subprocess

from .promotion import Artifact


class BuildFailure(RuntimeError):
    """Raised when a controlled package build cannot produce trusted evidence."""


@dataclass(frozen=True)
class BuildResult:
    artifact: Artifact
    evidence: dict[str, object]
    stdout: str
    stderr: str
    returncode: int


def _executable(command: str, label: str) -> str:
    resolved = shutil.which(command)
    if resolved is None:
        raise BuildFailure(f"{label} is unavailable: {command}")
    return resolved


def build_package(
    *,
    package_dir: Path,
    architecture: str,
    build_id: str,
    tests_passed: bool = False,
    makepkg_executable: str = "makepkg",
    signature_verifier: str = "pacman-key",
) -> BuildResult:
    """Run one makepkg build and return evidence tied to its output bytes.

    The caller must supply the result of an independent package test run. A
    successful makepkg process is not silently treated as runtime test proof.
    """
    if os.geteuid() == 0:
        raise BuildFailure("package builds must not run as root")
    if not package_dir.is_dir() or not (package_dir / "PKGBUILD").is_file():
        raise BuildFailure("package directory must contain PKGBUILD")
    if not architecture or not build_id:
        raise BuildFailure("architecture and build_id are required")
    if tests_passed is not True:
        raise BuildFailure("package tests did not pass")

    makepkg = _executable(makepkg_executable, "makepkg")
    try:
        process = subprocess.run(
            [makepkg, "--syncdeps", "--cleanbuild", "--clean", "--noconfirm"],
            cwd=package_dir,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise BuildFailure(f"makepkg could not execute: {exc}") from exc
    if process.returncode != 0:
        raise BuildFailure(f"makepkg failed with exit code {process.returncode}")

    artifacts = sorted(
        path for path in package_dir.glob("*.pkg.tar.*") if not path.name.endswith(".sig")
    )
    if len(artifacts) != 1:
        raise BuildFailure(f"expected exactly one package artifact, found {len(artifacts)}")
    artifact_path = artifacts[0]
    signature_path = artifact_path.with_name(artifact_path.name + ".sig")
    if not signature_path.is_file():
        raise BuildFailure("package signature is missing")

    verifier = _executable(signature_verifier, "signature verifier")
    try:
        signature = subprocess.run(
            [verifier, "--verify", str(signature_path), str(artifact_path)],
            cwd=package_dir,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise BuildFailure(f"signature verifier could not execute: {exc}") from exc
    if signature.returncode != 0:
        raise BuildFailure("package signature verification failed")

    digest = "sha256:" + hashlib.sha256(artifact_path.read_bytes()).hexdigest()
    artifact = Artifact(
        name=artifact_path.name.split("-")[0],
        version="unknown",
        architecture=architecture,
        digest=digest,
        source_path=str(artifact_path),
    )
    evidence = {
        "artifact_digest": digest,
        "architecture": architecture,
        "build_id": build_id,
        "signature_valid": True,
        "tests_passed": True,
    }
    return BuildResult(
        artifact=artifact,
        evidence=evidence,
        stdout=process.stdout,
        stderr=process.stderr,
        returncode=process.returncode,
    )
