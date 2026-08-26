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

This is not a package manager and does not build, sign, publish, or install packages. It is the receipt and gate substrate that those adapters can call.

## Run

```bash
python3 -m pytest -q
python3 verify.py
```

The demo hashes a temporary artifact file. The next slice should replace that fixture with a real Arch package produced by a controlled build adapter, while keeping this gate contract unchanged.
