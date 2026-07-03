# Release Governance

This repository publishes a curated public kernel demonstrator. Release process
controls are intentionally narrow: they protect the public kernel surface without
claiming production readiness, compliance, official signing, or supply-chain
attestation.

## Immutable Release Tags

Release tags are immutable once pushed to `origin`.

Do not delete, recreate, or force-push a published `v*` tag. Do not use
`git push --force --tags`, `git tag -d <tag>` followed by remote deletion, or any
other retag flow for a public release.

If a release tag is wrong, leave the original tag in place and publish a new patch
release with a correction note. The GitHub Release text may add a clearly dated
erratum, but the tag target must not move.

Use annotated SemVer tags for public releases, for example:

```bash
git tag -a v0.1.2 -m "AOS Kernel v0.1.2"
git push origin v0.1.2
```

## Required Repository Controls

Before publishing a public release, manually verify the repository-hosted
settings because local validation cannot prove them.

Recommended `main` protection:

- active branch ruleset or branch protection rule targeting `main`;
- required status check: `AOS Kernel CI / validate` from GitHub Actions;
- strict/up-to-date status checks when practical;
- pull request required before merge for non-emergency changes;
- force pushes and deletions blocked;
- no routine admin bypass for release commits.

Recommended release tag protection:

- active tag ruleset targeting `v*`;
- restrict updates and deletions;
- restrict creations to release maintainers if the repository role allows it;
- block force pushes.

If a tag ruleset is not yet configured, this documented no-retag policy is the
minimum public repository policy. It is weaker than enforced tag protection and
must be called out during release review.

## GitHub Release Publication

GitHub Releases are published from the checked-in release note drafts under
`docs/releases/`. Publish only after the tag exists, the final commit CI is green,
and the local release gate passes.

For existing release drafts:

- publish `docs/releases/v0.1.0.md` against tag `v0.1.0`;
- publish `docs/releases/v0.1.1.md` against tag `v0.1.1`;
- mark only the highest current patch release as the latest release;
- attach no binary artifact, SBOM, attestation, or signature unless the
  corresponding audited infrastructure exists.

Release text must keep the same public boundary as the repository: abstract Lean
model, Python demonstrator, reproducible fixture evidence, Trusted Output v0 as
`UNSIGNED_NOT_OFFICIAL`, and no production/compliance/signing claim.

## Operational Handoff

After `v0.1.1`, keep `aos-kernel` focused on kernel code, tests, evidence,
release notes, and formal surface. Workflow-product experiments belong in
`aos-workflow-gate` unless they are required to preserve the public kernel
contract.