from __future__ import annotations

import tools.audit_precheck as audit_precheck


def test_project_version_parser_reads_project_table_only() -> None:
    payload = """
[build-system]
requires = ["demo==1"]

[project]
name = "aos-kernel"
version = "0.1.1"

[tool.demo]
version = "9.9.9"
"""

    assert audit_precheck.parse_project_version(payload) == "0.1.1"


def test_workflow_action_refs_reports_non_sha_refs() -> None:
    workflow = """
steps:
  - uses: actions/checkout@v4
  - uses: owner/action@0123456789abcdef0123456789abcdef01234567
  - uses: ./.github/actions/local
"""

    assert audit_precheck.unpinned_workflow_actions(workflow) == [
        "actions/checkout@v4"
    ]


def test_current_repository_audit_precheck_has_no_failures() -> None:
    findings = audit_precheck.run_precheck(audit_precheck.PrecheckConfig())

    failures = [finding for finding in findings if finding.severity == "FAIL"]

    assert failures == []
