# Audit Precheck

`tools/audit_precheck.py` is a local release-surface precheck for the curated
public AOS Kernel repository. It catches avoidable publication blockers before a
commit, tag, or release review.

It is not a certification, compliance attestation, SLSA claim, SSDF claim,
security audit, production-readiness claim, or official signing check.

## Commands

General repository precheck:

```bash
python tools/audit_precheck.py
```

Strict local release precheck:

```bash
python tools/audit_precheck.py --release-version 0.1.1
```

Optional remote-aware release precheck before tag creation:

```bash
python tools/audit_precheck.py --release-version 0.1.1 --check-remote
```

`--check-remote` requires network access and checks `origin/main` plus the
remote release tag namespace. Use it immediately before creating a future
annotated release tag.

## What It Checks

- Git state: repository root, branch, official origin URL, dirty working tree,
  local release tag absence, and optional remote tag absence.
- Version coherence: `VERSION`, `pyproject.toml`, README public demonstrator
  version, and SemVer-compatible release input.
- Documentation map: `docs.json` lists existing public documents and keeps the
  curated public kernel role.
- Public claim boundary: no stale trust-wording and required negative
  production, compliance, security, signing, and refinement boundaries remain.
- Trusted Output v0: the public fixture remains `UNSIGNED_NOT_OFFICIAL`,
  `official_aos_output: false`, and all public claim-boundary flags are false.
- Integrity: delegates to `tools/verify_public_integrity.py`.
- Lean surface: public Lean files avoid gap terms such as `sorry` and `admit`.
- CI shape: minimal permissions, no privileged PR triggers, checkout credentials
  disabled, canonical standard gate invoked, third-party actions pinned to full
  commit SHA values, and Dependabot configured for Actions and Python updates
  while routing major updates to manual review.

## Severity Model

`FAIL` means the release surface should not be tagged until fixed.

`WARN` means useful audit-hardening context that may not block local development.
Use `--warnings-as-errors` when preparing for a stricter external audit.

## Manual Checks Still Required

Local precheck cannot prove repository-hosted controls. Before tagging a public
release, manually verify:

- latest GitHub Actions run for the final commit is green;
- `main` has branch protection or a ruleset with required status checks;
- release tag protection or a documented no-retag policy is in place;
- GitHub About, Topics, and release notes match the public demonstrator claim;
- no official package, SBOM, attestation, or signing claim is published unless
  the corresponding infrastructure exists and is separately audited.
