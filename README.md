# Omarchy Package Stewardship

A small, deterministic prototype for the trust-critical part of the proposed Omarchy package-stewardship architecture.

## First working slice

This prototype models one question:

> After a regression, can a maintainer identify the exact stable artifact and roll back without guessing?

It currently provides:

- edge-to-stable promotion only when test evidence names the exact candidate digest;
- a promotion receipt preserving the previous stable digest;
- rollback receipts that point back to the promotion receipt and previous artifact;
- rejection of mismatched artifact evidence and failed tests.

This is not a package manager and does not build, sign, publish, or install packages. It is the receipt and gate substrate that those adapters can call.

## Run

```bash
python3 -m pytest -q
python3 verify.py
```

The next slice should replace synthetic digests with real package files and attach native build, signature, and architecture evidence without changing the gate contract.
