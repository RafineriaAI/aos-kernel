from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
PUBLIC_ROLE = "curated_public_kernel_release_surface"
EXPECTED_RELEASE_BRANCH = "main"
EXPECTED_REMOTE_URLS = {
    "https://github.com/RafineriaAI/aos-kernel.git",
    "git@github.com:RafineriaAI/aos-kernel.git",
}
TRUSTED_OUTPUT_FIXTURE = "examples/reports/public-replay-trusted-output.json"
FULL_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\."
    r"(0|[1-9]\d*)\."
    r"(0|[1-9]\d*)"
    r"(?:-((?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*))*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)
USES_RE = re.compile(r"\buses:\s*([^\s#]+)")

REQUIRED_DOCS = {
    "README.md",
    "EVIDENCE.md",
    "INTEGRATION.md",
    "SCOPE_OF_PROOF.md",
    "COMMERCIAL_BOUNDARY.md",
    "docs/AUDIT_PRECHECK.md",
    "docs/TRUSTED_AOS_OUTPUT.md",
    "docs/FORMAL_CLAIMS_BOUNDARY.md",
    "docs/PUBLIC_BOUNDARY.md",
    "docs/PROOF_OF_VALUE.md",
    "docs/VALIDATION_GATES.md",
    "docs/case-studies/public-repo-replay.md",
    "docs/releases/v0.1.0.md",
    "docs/releases/v0.1.1.md",
    "examples/reports/public-replay-summary.md",
}
REQUIRED_BOUNDARY_TEXT = {
    "README.md": (
        "signature_status: UNSIGNED_NOT_OFFICIAL",
        "official_aos_output: false",
        "It does not prove production readiness",
        "Python-Lean refinement correctness",
    ),
    "SCOPE_OF_PROOF.md": (
        "Python-to-Lean refinement",
        "production security or deployment readiness",
        "external validation or independent assessment",
    ),
    "docs/TRUSTED_AOS_OUTPUT.md": (
        "UNSIGNED_NOT_OFFICIAL",
        "official_aos_output: false",
        "Trusted Output v0 does not claim production readiness",
        "SLSA compliance",
    ),
    "docs/FORMAL_CLAIMS_BOUNDARY.md": (
        "abstract public verdict model",
        "not a Python-Lean refinement claim",
        "The Lean layer proves production runtime correctness.",
    ),
}
EXPECTED_FALSE_CLAIMS = {
    "official_signed_verdict_claim",
    "cryptographic_signature_claim",
    "identity_assurance_claim",
    "slsa_compliance_claim",
    "tuf_root_claim",
    "rekor_transparency_log_claim",
    "production_readiness_claim",
    "security_audit_claim",
    "security_warranty_claim",
}
FORBIDDEN_TRACKED_PREFIXES = (
    ".benchmarks/",
    ".hypothesis/",
    ".lake/",
    ".mypy_cache/",
    ".ruff_cache/",
    ".tmp/",
)
FORBIDDEN_TRACKED_SUFFIXES = (".pyc", ".pyo", ".so", ".dll", ".exe")
FORBIDDEN_PUBLIC_TEXT = ("trust status", "expected trust status")


@dataclass(frozen=True)
class PrecheckConfig:
    release_version: str | None = None
    check_remote: bool = False
    warnings_as_errors: bool = False


@dataclass(frozen=True)
class Finding:
    severity: str
    check_id: str
    message: str


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


def run_command(args: Sequence[str]) -> CommandResult:
    result = subprocess.run(
        list(args),
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return CommandResult(
        result.returncode,
        result.stdout.strip(),
        result.stderr.strip(),
    )


def git(args: Sequence[str]) -> CommandResult:
    return run_command(["git", *args])


def add(
    findings: list[Finding],
    severity: str,
    check_id: str,
    message: str,
) -> None:
    findings.append(Finding(severity, check_id, message))


def release_severity(config: PrecheckConfig) -> str:
    return "FAIL" if config.release_version is not None else "WARN"


def read_text(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def read_json_object(path: str) -> dict[str, Any]:
    payload = json.loads(read_text(path))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must be a JSON object")
    return payload


def parse_project_version(pyproject_text: str) -> str | None:
    in_project = False
    for line in pyproject_text.splitlines():
        stripped = line.strip()
        if stripped == "[project]":
            in_project = True
            continue
        if stripped.startswith("[") and stripped.endswith("]"):
            in_project = False
        if not in_project:
            continue
        match = re.match(r'version\s*=\s*"([^"]+)"', stripped)
        if match:
            return match.group(1)
    return None


def tracked_paths() -> list[str]:
    result = git(["ls-files"])
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line]


def tracked_text(path: str) -> str | None:
    data = (REPO_ROOT / path).read_bytes()
    if b"\0" in data:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def workflow_action_refs(workflow_text: str) -> list[str]:
    return USES_RE.findall(workflow_text)


def unpinned_workflow_actions(workflow_text: str) -> list[str]:
    unpinned: list[str] = []
    for action_ref in workflow_action_refs(workflow_text):
        if action_ref.startswith("./") or action_ref.startswith(".\\"):
            continue
        if "@" not in action_ref:
            unpinned.append(action_ref)
            continue
        ref = action_ref.rsplit("@", 1)[1]
        if FULL_SHA_RE.fullmatch(ref) is None:
            unpinned.append(action_ref)
    return unpinned


def check_git_state(config: PrecheckConfig, findings: list[Finding]) -> None:
    root = git(["rev-parse", "--show-toplevel"])
    if root.returncode != 0:
        add(findings, "FAIL", "git.root", "repository root cannot be resolved")
        return
    if Path(root.stdout).resolve() != REPO_ROOT.resolve():
        add(findings, "FAIL", "git.root", "unexpected repository root")

    branch = git(["branch", "--show-current"])
    branch_name = branch.stdout.strip()
    if branch.returncode != 0 or not branch_name:
        add(findings, release_severity(config), "git.branch", "current branch unknown")
    elif branch_name != EXPECTED_RELEASE_BRANCH:
        add(
            findings,
            release_severity(config),
            "git.branch",
            f"current branch is {branch_name}, expected {EXPECTED_RELEASE_BRANCH}",
        )

    origin = git(["remote", "get-url", "origin"])
    origin_url = origin.stdout.strip()
    if origin.returncode != 0 or not origin_url:
        add(findings, release_severity(config), "git.origin", "origin remote missing")
    elif origin_url not in EXPECTED_REMOTE_URLS:
        add(
            findings,
            release_severity(config),
            "git.origin",
            f"unexpected origin {origin_url}",
        )

    status = git(["status", "--porcelain=v1"])
    lines = [line for line in status.stdout.splitlines() if line]
    if status.returncode != 0:
        add(findings, "FAIL", "git.status", "git status failed")
    elif lines:
        preview = "; ".join(lines[:5])
        add(findings, release_severity(config), "git.clean", f"dirty tree: {preview}")


def check_release_tag(config: PrecheckConfig, findings: list[Finding]) -> None:
    if config.release_version is None:
        return
    version = config.release_version
    tag = f"v{version}"
    if SEMVER_RE.fullmatch(version) is None:
        add(findings, "FAIL", "release.semver", f"{version} is not SemVer 2.0.0")
        return
    local_tag = git(["rev-parse", "-q", "--verify", f"refs/tags/{tag}"])
    if local_tag.returncode == 0:
        add(findings, "FAIL", "release.tag.local", f"local tag {tag} already exists")
    if not config.check_remote:
        add(findings, "WARN", "release.remote", "remote tag state not checked")
        return
    remote = git(
        [
            "ls-remote",
            "origin",
            f"refs/tags/{tag}",
            f"refs/tags/{tag}^{{}}",
            f"refs/heads/{EXPECTED_RELEASE_BRANCH}",
        ]
    )
    if remote.returncode != 0:
        add(findings, "FAIL", "release.remote", remote.stderr or remote.stdout)
        return
    for line in remote.stdout.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1].startswith(f"refs/tags/{tag}"):
            add(findings, "FAIL", "release.tag.remote", f"remote tag {tag} exists")


def check_version(config: PrecheckConfig, findings: list[Finding]) -> None:
    version = read_text("VERSION").strip()
    project_version = parse_project_version(read_text("pyproject.toml"))
    if SEMVER_RE.fullmatch(version) is None:
        add(findings, "FAIL", "version.semver", f"VERSION is not SemVer: {version}")
    if project_version != version:
        add(findings, "FAIL", "version.pyproject", "pyproject version mismatch")
    if config.release_version is not None and config.release_version != version:
        add(findings, "FAIL", "version.release", "release version mismatch")
    if f"Public demonstrator version: `{version}`" not in read_text("README.md"):
        add(findings, "FAIL", "version.readme", "README version mismatch")
    if f'FALLBACK_AOS_VERSION: Final = "{version}"' not in read_text(
        "aos_cli/trusted_output.py"
    ):
        add(findings, "FAIL", "version.trusted-output", "fallback version mismatch")


def check_docs_index(findings: list[Finding]) -> None:
    docs = read_json_object("docs.json")
    if docs.get("schema_version") != "aos-kernel-docs/v1":
        add(findings, "FAIL", "docs.schema", "docs.json schema_version mismatch")
    if docs.get("repository_role") != PUBLIC_ROLE:
        add(findings, "FAIL", "docs.role", "docs.json repository_role mismatch")
    documents = docs.get("documents")
    if not isinstance(documents, list):
        add(findings, "FAIL", "docs.documents", "documents must be a list")
        return
    paths: list[str] = []
    for item in documents:
        if not isinstance(item, dict):
            add(findings, "FAIL", "docs.entry", "document entry is not object")
            continue
        path = item.get("path")
        if not isinstance(path, str) or not path:
            add(findings, "FAIL", "docs.path", "document path invalid")
            continue
        paths.append(path)
        if not (REPO_ROOT / path).is_file():
            add(findings, "FAIL", "docs.exists", f"indexed document missing: {path}")
    indexed = set(paths)
    for required in sorted(REQUIRED_DOCS.difference(indexed)):
        add(findings, "FAIL", "docs.required", f"docs.json missing {required}")


def check_claim_boundary(findings: list[Finding]) -> None:
    for path, snippets in REQUIRED_BOUNDARY_TEXT.items():
        text = read_text(path)
        for snippet in snippets:
            if snippet not in text:
                add(
                    findings,
                    "FAIL",
                    "claims.boundary-text",
                    f"{path} missing {snippet}",
                )
    for path in tracked_paths():
        if not (path.endswith(".md") or path in {"README.md", "EVIDENCE.md"}):
            continue
        public_text = tracked_text(path)
        if public_text is None:
            continue
        lowered = public_text.lower()
        for phrase in FORBIDDEN_PUBLIC_TEXT:
            if phrase in lowered:
                add(findings, "FAIL", "claims.stale-wording", f"{phrase!r} in {path}")


def check_trusted_output_fixture(findings: list[Finding]) -> None:
    output = read_json_object(TRUSTED_OUTPUT_FIXTURE)
    if output.get("signature_status") != "UNSIGNED_NOT_OFFICIAL":
        add(findings, "FAIL", "trusted-output.status", "fixture must stay unsigned")
    if output.get("official_aos_output") is not False:
        add(findings, "FAIL", "trusted-output.official", "fixture must not be official")
    if output.get("issuer_trust_status") != "UNVERIFIED":
        add(findings, "FAIL", "trusted-output.issuer", "issuer must remain unverified")
    boundary = output.get("claim_boundary")
    if not isinstance(boundary, dict):
        add(findings, "FAIL", "trusted-output.claims", "claim boundary missing")
        return
    for claim in sorted(EXPECTED_FALSE_CLAIMS):
        if boundary.get(claim) is not False:
            add(findings, "FAIL", "trusted-output.claims", f"{claim} must be false")


def check_lean_surface(findings: list[Finding]) -> None:
    lakefile = read_text("lakefile.lean")
    for root in ("AOSPublicCore", "AOSEnvironmentModel", "AOSAxiomAudit"):
        if root not in lakefile:
            add(findings, "FAIL", "lean.lakefile", f"{root} missing from lakefile")
    if "#print axioms" not in read_text("lean/AOSAxiomAudit.lean"):
        add(findings, "FAIL", "lean.axiom-audit", "dependency report missing")
    for path in sorted((REPO_ROOT / "lean").glob("*.lean")):
        lines = path.read_text(encoding="utf-8").splitlines()
        for line_number, line in enumerate(lines, 1):
            code = line.split("--", 1)[0]
            relative = path.relative_to(REPO_ROOT)
            if re.search(r"\b(sorry|admit)\b", code):
                add(findings, "FAIL", "lean.gap-term", f"{relative}:{line_number}")
            if re.match(r"\s*(axiom|constant)\b", code):
                add(
                    findings,
                    "FAIL",
                    "lean.axiom-declaration",
                    f"{relative}:{line_number}",
                )
            if re.match(r"\s*unsafe\b", code):
                add(findings, "FAIL", "lean.unsafe", f"{relative}:{line_number}")


def check_ci(findings: list[Finding]) -> None:
    workflow = read_text(".github/workflows/aos-kernel-ci.yml").replace("\r\n", "\n")
    if "permissions:\n  contents: read" not in workflow:
        add(findings, "FAIL", "ci.permissions", "contents: read missing")
    if "persist-credentials: false" not in workflow:
        add(findings, "FAIL", "ci.checkout", "persist-credentials false missing")
    if "python tools/run_validation_gate.py --standard --skip-install" not in workflow:
        add(findings, "FAIL", "ci.standard-gate", "standard gate missing")
    for trigger in ("pull_request_target", "workflow_run"):
        if trigger in workflow:
            add(findings, "FAIL", "ci.privileged-trigger", f"{trigger} not allowed")
    if "self-hosted" in workflow:
        add(findings, "FAIL", "ci.runner", "self-hosted runner not allowed")
    if "secrets." in workflow:
        add(findings, "WARN", "ci.secrets", "workflow references secrets")
    for action_ref in unpinned_workflow_actions(workflow):
        add(findings, "FAIL", "ci.action-pin", f"{action_ref} is not pinned")


def check_dependabot(findings: list[Finding]) -> None:
    path = REPO_ROOT / ".github" / "dependabot.yml"
    if not path.is_file():
        add(findings, "FAIL", "dependabot.config", "dependabot.yml missing")
        return
    config = path.read_text(encoding="utf-8")
    required = (
        "version: 2",
        'package-ecosystem: "github-actions"',
        'package-ecosystem: "pip"',
        'directory: "/"',
        "interval: \"weekly\"",
    )
    for snippet in required:
        if snippet not in config:
            add(
                findings,
                "FAIL",
                "dependabot.config",
                f"dependabot.yml missing {snippet}",
            )


def check_public_surface(findings: list[Finding]) -> None:
    paths = tracked_paths()
    if not paths:
        add(findings, "FAIL", "git.ls-files", "cannot enumerate tracked files")
        return
    for path in paths:
        normalized = path.replace("\\", "/")
        if normalized.startswith(FORBIDDEN_TRACKED_PREFIXES):
            add(
                findings,
                "FAIL",
                "surface.tracked-artifact",
                f"tracked artifact: {path}",
            )
        if normalized.endswith(FORBIDDEN_TRACKED_SUFFIXES):
            add(findings, "FAIL", "surface.tracked-binary", f"tracked binary: {path}")


def check_integrity(findings: list[Finding]) -> None:
    result = run_command([sys.executable, "tools/verify_public_integrity.py"])
    if result.returncode != 0:
        output = result.stderr or result.stdout or "integrity check failed"
        add(findings, "FAIL", "integrity.manifest", output.splitlines()[0])


def run_precheck(config: PrecheckConfig) -> list[Finding]:
    findings: list[Finding] = []
    checks = (
        lambda: check_git_state(config, findings),
        lambda: check_release_tag(config, findings),
        lambda: check_version(config, findings),
        lambda: check_docs_index(findings),
        lambda: check_claim_boundary(findings),
        lambda: check_trusted_output_fixture(findings),
        lambda: check_lean_surface(findings),
        lambda: check_ci(findings),
        lambda: check_dependabot(findings),
        lambda: check_public_surface(findings),
        lambda: check_integrity(findings),
    )
    for check in checks:
        try:
            check()
        except Exception as exc:  # pragma: no cover - defensive report boundary.
            add(findings, "FAIL", "precheck.internal", str(exc))
    return findings


def print_text_report(findings: list[Finding], config: PrecheckConfig) -> None:
    print("AOS audit precheck")
    if config.release_version is not None:
        print(f"Release version: {config.release_version}")
    if not findings:
        print("[PASS] no findings")
        return
    for finding in findings:
        print(f"[{finding.severity}] {finding.check_id}: {finding.message}")
    failures = [finding for finding in findings if finding.severity == "FAIL"]
    warnings = [finding for finding in findings if finding.severity == "WARN"]
    print(f"Summary: {len(failures)} failure(s), {len(warnings)} warning(s)")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the AOS Kernel release-surface audit precheck."
    )
    parser.add_argument("--release-version")
    parser.add_argument("--check-remote", action="store_true")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--warnings-as-errors", action="store_true")
    args = parser.parse_args(argv)
    config = PrecheckConfig(
        release_version=args.release_version,
        check_remote=args.check_remote,
        warnings_as_errors=args.warnings_as_errors,
    )
    findings = run_precheck(config)
    failures = [finding for finding in findings if finding.severity == "FAIL"]
    warnings = [finding for finding in findings if finding.severity == "WARN"]
    if args.as_json:
        payload = {
            "schema_version": "aos-kernel-audit-precheck/v1",
            "repository_role": PUBLIC_ROLE,
            "release_version": config.release_version,
            "check_remote": config.check_remote,
            "summary": {"failures": len(failures), "warnings": len(warnings)},
            "findings": [asdict(finding) for finding in findings],
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print_text_report(findings, config)
    if failures:
        return 1
    if config.warnings_as_errors and warnings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
