#!/usr/bin/env python3
"""Tests for Phase 3 documentation updates (task-12).

Verifies that BUNDLE_AUTHORING.md, REGISTRY.md, and README.md
have been updated with all Phase 3 deliverables.

Run with: pytest torque/test/test_phase3_docs.py
"""

import re
from pathlib import Path

# File paths relative to repo root
REPO = Path(__file__).parent.parent
BUNDLE_AUTHORING = REPO / "docs" / "BUNDLE_AUTHORING.md"
REGISTRY = REPO / "REGISTRY.md"
README = REPO / "README.md"

# Read each file once at module load; all tests share these cached strings.
_CONTENT: dict[Path, str] = {
    BUNDLE_AUTHORING: BUNDLE_AUTHORING.read_text(),
    REGISTRY: REGISTRY.read_text(),
    README: README.read_text(),
}


def count_code_fences(content: str) -> int:
    """Count occurrences of triple backticks in content."""
    return len(re.findall(r"```", content))


# ─────────────────────────────────────────────────────────────────────────────
# BUNDLE_AUTHORING.md tests
# ─────────────────────────────────────────────────────────────────────────────


def test_bundle_authoring_realtime_channels_heading():
    content = _CONTENT[BUNDLE_AUTHORING]
    assert "### Realtime Channels" in content, "Missing '### Realtime Channels' heading"


def test_bundle_authoring_realtime_channels_intro():
    content = _CONTENT[BUNDLE_AUTHORING]
    assert (
        "Declare WebSocket channels in your manifest to enable real-time push:"
        in content
    ), "Missing Realtime Channels intro sentence"


def test_bundle_authoring_realtime_channels_yaml():
    content = _CONTENT[BUNDLE_AUTHORING]
    assert "realtime:" in content, "Missing 'realtime:' YAML key in BUNDLE_AUTHORING.md"
    assert "channels:" in content, "Missing 'channels:' YAML key in BUNDLE_AUTHORING.md"


def test_bundle_authoring_realtime_channels_name_template():
    content = _CONTENT[BUNDLE_AUTHORING]
    assert "replaced from payload" in content, (
        "Missing explanation of channel name template replacement from payload"
    )


def test_bundle_authoring_realtime_channels_wildcard():
    content = _CONTENT[BUNDLE_AUTHORING]
    assert "wildcard" in content.lower(), (
        "Missing wildcard explanation for event patterns"
    )


def test_bundle_authoring_realtime_channels_auth():
    content = _CONTENT[BUNDLE_AUTHORING]
    assert "true/false" in content or "returning true/false" in content, (
        "Missing auth interface description (returning true/false)"
    )


def test_bundle_authoring_realtime_channels_closing():
    content = _CONTENT[BUNDLE_AUTHORING]
    assert "No code needed in your bundle" in content, (
        "Missing closing line 'No code needed in your bundle'"
    )


def test_bundle_authoring_agent_intents_heading():
    content = _CONTENT[BUNDLE_AUTHORING]
    assert "### Agent Intents" in content, "Missing '### Agent Intents' heading"


def test_bundle_authoring_agent_intents_intro():
    content = _CONTENT[BUNDLE_AUTHORING]
    assert "Define intents in your bundle for LLM-driven execution:" in content, (
        "Missing Agent Intents intro sentence"
    )


def test_bundle_authoring_agent_intents_yaml():
    content = _CONTENT[BUNDLE_AUTHORING]
    assert "intents:" in content, "Missing 'intents:' YAML key in BUNDLE_AUTHORING.md"


def test_bundle_authoring_agent_intents_js_example():
    content = _CONTENT[BUNDLE_AUTHORING]
    assert all(term in content for term in ("Intent", "Behavior", "Context")), (
        "Missing one or more JS example class references: Intent, Behavior, Context"
    )


def test_bundle_authoring_agent_intents_closing():
    content = _CONTENT[BUNDLE_AUTHORING]
    assert "POST /api/intents/" in content, (
        "Missing 'POST /api/intents/{bundle}/{intent}' endpoint reference"
    )
    assert "@anthropic-ai/claude-agent-sdk" in content, (
        "Missing @anthropic-ai/claude-agent-sdk requirement"
    )
    assert "ANTHROPIC_API_KEY" in content, "Missing ANTHROPIC_API_KEY requirement"


def test_bundle_authoring_embeddings_heading():
    content = _CONTENT[BUNDLE_AUTHORING]
    assert "### Embeddings Configuration" in content, (
        "Missing '### Embeddings Configuration' heading"
    )


def test_bundle_authoring_embeddings_intro():
    content = _CONTENT[BUNDLE_AUTHORING]
    assert "Enable vector search in your mount plan:" in content, (
        "Missing Embeddings Configuration intro sentence"
    )


def test_bundle_authoring_embeddings_yaml():
    content = _CONTENT[BUNDLE_AUTHORING]
    assert "embeddings:" in content, "Missing 'embeddings:' YAML key"
    assert "provider:" in content, "Missing 'provider:' YAML key in embeddings config"
    assert "store:" in content, "Missing 'store:' YAML key in embeddings config"
    assert "local" in content, "Missing 'local' provider option"
    assert "sqlite" in content, "Missing 'sqlite' store option"


def test_bundle_authoring_code_fences_balanced():
    content = _CONTENT[BUNDLE_AUTHORING]
    count = count_code_fences(content)
    assert count % 2 == 0, (
        f"Unbalanced code fences in BUNDLE_AUTHORING.md: {count} occurrences (must be even)"
    )


# ─────────────────────────────────────────────────────────────────────────────
# REGISTRY.md tests
# ─────────────────────────────────────────────────────────────────────────────


def test_registry_phase3_section():
    content = _CONTENT[REGISTRY]
    assert "Phase 3" in content, "Missing 'Phase 3' section heading in REGISTRY.md"


def test_registry_ext_embeddings():
    content = _CONTENT[REGISTRY]
    assert "ext-embeddings" in content, (
        "Missing 'ext-embeddings' extension in REGISTRY.md"
    )


def test_registry_ext_otel():
    content = _CONTENT[REGISTRY]
    assert "ext-otel" in content, "Missing 'ext-otel' extension in REGISTRY.md"


def test_registry_ext_security():
    content = _CONTENT[REGISTRY]
    assert "ext-security" in content, "Missing 'ext-security' extension in REGISTRY.md"


def test_registry_behaviors_table_observability():
    content = _CONTENT[REGISTRY]
    assert "observability" in content, (
        "Missing 'observability' behavior in REGISTRY.md behaviors table"
    )


def test_registry_behaviors_table_security_hardened():
    content = _CONTENT[REGISTRY]
    assert "security-hardened" in content, (
        "Missing 'security-hardened' behavior in REGISTRY.md behaviors table"
    )


def test_registry_code_fences_balanced():
    content = _CONTENT[REGISTRY]
    count = count_code_fences(content)
    assert count % 2 == 0, (
        f"Unbalanced code fences in REGISTRY.md: {count} occurrences (must be even)"
    )


# ─────────────────────────────────────────────────────────────────────────────
# README.md tests
# ─────────────────────────────────────────────────────────────────────────────


def test_readme_agent_runtime_heading():
    content = _CONTENT[README]
    assert "### Agent Runtime" in content, (
        "Missing '### Agent Runtime' section in README.md"
    )


def test_readme_agent_runtime_endpoint():
    content = _CONTENT[README]
    assert "/api/intents/" in content, (
        "Missing /api/intents/ endpoint reference in README.md Agent Runtime section"
    )


def test_readme_agent_runtime_claude():
    content = _CONTENT[README]
    assert "ClaudeRuntime" in content or "claude-agent-sdk" in content, (
        "Missing ClaudeRuntime/claude-agent-sdk reference in README.md"
    )


def test_readme_agent_runtime_manifest_features():
    content = _CONTENT[README]
    assert "success criteria" in content or "allowed tools" in content, (
        "Missing manifest intent features (success criteria / allowed tools) in README.md"
    )


def test_readme_observability_security_heading():
    content = _CONTENT[README]
    assert "### Observability & Security" in content, (
        "Missing '### Observability & Security' section in README.md"
    )


def test_readme_observability_otel():
    content = _CONTENT[README]
    assert "OTel" in content or "OpenTelemetry" in content, (
        "Missing OTel/OpenTelemetry reference in README.md Observability section"
    )


def test_readme_observability_rbac():
    content = _CONTENT[README]
    assert "RBAC" in content, (
        "Missing RBAC reference in README.md Observability & Security section"
    )


def test_readme_observability_rate_limiting():
    content = _CONTENT[README]
    lower = content.lower()
    assert "rate limit" in lower or "rate_limit" in lower, (
        "Missing rate limiting reference in README.md Observability & Security section"
    )


def test_readme_observability_csrf():
    content = _CONTENT[README]
    assert "CSRF" in content, (
        "Missing CSRF reference in README.md Observability & Security section"
    )


def test_readme_observability_audit():
    content = _CONTENT[README]
    assert "audit" in content.lower(), (
        "Missing audit logging reference in README.md Observability & Security section"
    )


def test_readme_code_fences_balanced():
    content = _CONTENT[README]
    count = count_code_fences(content)
    assert count % 2 == 0, (
        f"Unbalanced code fences in README.md: {count} occurrences (must be even)"
    )
