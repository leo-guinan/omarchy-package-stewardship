# Omarchy Package Stewardship

A small, deterministic prototype for the trust-critical part of the proposed Omarchy package-stewardship architecture.

## First working slice

This prototype models one question:

> After a regression, can a maintainer identify the exact stable artifact and roll back without guessing?

It currently provides:

- edge-to-stable promotion only when test evidence names the exact candidate digest;
- SHA-256 digests computed from artifact file bytes rather than trusted declarations;
- required build ID, architecture, signature-valid, and test-pass evidence;
- a promotion receipt preserving the previous stable digest;
- rollback receipts that point back to the promotion receipt and previous artifact;
- rejection of mismatched artifact evidence and failed tests.

## Controlled build adapter

`omarchy_stewardship.build.build_package` is the next boundary. It runs one
`makepkg` invocation without a shell, refuses root execution, requires a
`PKGBUILD`, requires exactly one `.pkg.tar.*` output and its adjacent `.sig`,
invokes a separate signature verifier, hashes the resulting bytes, and records
the build ID, architecture, signature, and independently supplied package-test
result.

The test suite uses controlled executable fixtures to exercise that contract.
This macOS host does not have Arch's `makepkg`, so it does not claim to have
built a real Arch package locally. Run the adapter on an Arch x86_64 or aarch64
builder for that evidence.

This is not a package manager and does not install or publish packages. The adapter invokes the host's `makepkg` and signature verifier, while the receipt layer records their evidence.

## Run

```bash
python3 -m pytest -q
python3 verify.py
```

The demo hashes a temporary artifact file; the adapter tests exercise the real
process boundary. The next slice is an Arch-builder run that produces a real
package and signature, while keeping this gate contract unchanged.
