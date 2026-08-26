import hashlib
import os
import stat

import pytest

from omarchy_stewardship.build import BuildFailure, build_package


def executable(path, body):
    path.write_text("#!/bin/sh\n" + body)
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return path


def test_build_adapter_hashes_output_and_records_verified_evidence(tmp_path):
    package_dir = tmp_path / "package"
    package_dir.mkdir()
    (package_dir / "PKGBUILD").write_text("pkgname=demo\npkgver=1.1\n")
    artifact = package_dir / "demo-1.1-1-aarch64.pkg.tar.zst"
    makepkg = executable(
        tmp_path / "makepkg",
        "printf 'built' > demo-1.1-1-aarch64.pkg.tar.zst\nprintf 'signature' > demo-1.1-1-aarch64.pkg.tar.zst.sig\n",
    )
    verifier = executable(tmp_path / "verify-signature", "exit 0\n")

    result = build_package(
        package_dir=package_dir,
        architecture="aarch64",
        build_id="build-001",
        tests_passed=True,
        makepkg_executable=str(makepkg),
        signature_verifier=str(verifier),
    )

    expected = "sha256:" + hashlib.sha256(artifact.read_bytes()).hexdigest()
    assert result.artifact.digest == expected
    assert result.artifact.source_path == str(artifact)
    assert result.evidence == {
        "artifact_digest": expected,
        "architecture": "aarch64",
        "build_id": "build-001",
        "signature_valid": True,
        "tests_passed": True,
    }
    assert result.returncode == 0


def test_build_adapter_rejects_missing_signature(tmp_path):
    package_dir = tmp_path / "package"
    package_dir.mkdir()
    (package_dir / "PKGBUILD").write_text("pkgname=demo\n")
    makepkg = executable(
        tmp_path / "makepkg",
        "printf 'built' > demo-1.1-1-aarch64.pkg.tar.zst\n",
    )

    with pytest.raises(BuildFailure, match="signature"):
        build_package(
            package_dir=package_dir,
            architecture="aarch64",
            build_id="build-001",
            tests_passed=True,
            makepkg_executable=str(makepkg),
            signature_verifier=str(tmp_path / "missing-verifier"),
        )


def test_build_adapter_refuses_root_execution(tmp_path, monkeypatch):
    package_dir = tmp_path / "package"
    package_dir.mkdir()
    (package_dir / "PKGBUILD").write_text("pkgname=demo\n")
    monkeypatch.setattr(os, "geteuid", lambda: 0)

    with pytest.raises(BuildFailure, match="root"):
        build_package(
            package_dir=package_dir,
            architecture="aarch64",
            build_id="build-001",
        )
