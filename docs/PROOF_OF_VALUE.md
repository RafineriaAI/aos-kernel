# Kernel Proof Of Value

This document is the shortest practical path for evaluating whether the public
AOS kernel contract is useful over one bounded workflow artifact. Product-level
workflow packaging belongs in [RafineriaAI/aos-workflow-gate](https://github.com/RafineriaAI/aos-workflow-gate).

Current stage:

```text
public kernel demonstrator -> self-serve bounded-artifact replay -> pilot candidate
```

The public kernel repository should be evaluated as a decision layer over bounded
signals, not as a scanner, model, agent framework, security audit, certification,
or production deployment.

## What To Run First

Start with the bundled external-artifact demo:

```bash
aos demo
```

Then run AOS on one artifact from your own workflow:

```bash
aos check --sarif audit.sarif --output-dir .tmp/aos-check
```

or bind the result to a commit for PR/CI review:

```bash
aos gate --sarif audit.sarif --source-commit <commit-sha> --output-dir .tmp/aos-gate
```

For a stronger self-serve proof, run External Replay on a pinned repository commit:

```bash
aos external-replay \
  --repo https://github.com/owner/repo \
  --commit <40-character-commit-sha> \
  --mode gate \
  --output-dir .tmp/aos-external-replay
```

This adds permission pre-checks, a baseline comparison, a workflow value estimator, privacy-boundary reporting and supply-chain evidence fields. See
[External Replay](EXTERNAL_REPLAY.md).


The useful output is:

```text
input artifact -> PASS/WARN/BLOCK -> summary -> JSONL evidence -> SHA-256
```

## What To Measure

For one workflow, record:

| Metric | Why it matters |
| --- | --- |
| time to first verdict | integration friction |
| decision latency | delay between raw scanner/CI output and review or merge action |
| `PASS` / `WARN` / `BLOCK` distribution | decision shape |
| finding count | review size |
| review/block load | reviewer burden |
| signals converted to one decision | workflow compression |
| unexpected `PASS` count | risky pass-through check |
| replay success | reproducibility |
| evidence coverage | auditability |
| sanitized evidence coverage | privacy-preserving publication fit |
| pinned commit and hash availability | supply-chain evidence readiness |
| operator notes | practical fit and false-review pressure |

## What Can Be Shared

For public or vendor review, share only sanitized evidence:

```text
repository label
commit
tool or signal source
verdict
decision
finding count
record SHA-256
summary path
JSONL record path
```

Do not publish secrets, private source code, proprietary scanner output,
customer workflow data, credentials, internal policy logic, or private findings.

## Current Public Proof

The repository includes a committed third-party SARIF workflow sample from
`CERT-Polska/mwdb-core`. It demonstrates:

- import of a real external scanner artifact;
- deterministic `PASS` / `WARN` / `BLOCK` decision output;
- JSONL evidence;
- record hash;
- replayable public artifacts.

This is a kernel reference adapter proof. It is not a security audit of the target
repository, independent validation, production-readiness proof, guaranteed ROI,
SLSA compliance claim, signed provenance claim, or claim that AOS improves the
upstream scanner.

## Stronger Next Proof

The next useful evidence step is one permissioned shadow run:

```text
one external workflow
  -> retained scanner, CI, RAG, agent, or review-queue artifacts
  -> AOS check/gate
  -> sanitized evidence
  -> review-load and risky-pass-through notes
```

The result should be narrow, replayable, and falsifiable. A failed or noisy pilot
is still useful if it shows where the input signal is weak, ambiguous, or too
costly to review.

## Boundaries

This proof-of-value path does not establish:

- production readiness;
- customer adoption;
- willingness to pay;
- no compliance or certification claim;
- target-repository security;
- general AOS effectiveness;
- correctness of the upstream model, scanner, or agent.

It establishes only whether the public AOS kernel pattern is useful enough to
inspect in one bounded workflow.
