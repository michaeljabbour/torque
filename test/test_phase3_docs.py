#!/usr/bin/env python3
"""Tests for Phase 3 documentation updates (task-12).

Verifies that BUNDLE_AUTHORING.md, REGISTRY.md, and README.md
have been updated with all Phase 3 deliverables.
"""
import re
import sys
from pathlib import Path

# File paths relative to repo root
REPO = Path(__file__).parent.parent
BUNDLE_AUTHORING = REPO / "docs" / "BUNDLE_AUTHORING.md"
REGISTRY = REPO / "REGISTRY.md"
README = REPO / "README.md"


def count_code_fences(content: str) -> int:
    """Count occurrences of triple backticks in content."""
    return len(re.findall(r"```", content))


# ──────────────────────────────────────────────────────────────────────────────
# BUNDLE_AUTHORING.md tests
# ──────────────────────────────────────────────────────────────────────────────

def test_bundle_authoring_realtime_channels_heading():
    content = BUNDLE_AUTHORING.read_text()
    assert "### Realtime Channels" in content, "Missing '### Realtime Channels' heading"


def test_bundle_authoring_realtime_channels_intro():
    content = BUNDLE_AUTHORING.read_text()
    assert "Declare WebSocket channels in your manifest to enable real-time push:" in content, \
        "Missing Realtime Channels intro sentence"


def test_bundle_authoring_realtime_channels_yaml():
    content = BUNDLE_AUTHORING.read_text()
    assert "realtime:" in content, "Missing 'realtime:' YAML key in BUNDLE_AUTHORING.md"
    assert "channels:" in content, "Missing 'channels:' YAML key in BUNDLE_AUTHORING.md"


def test_bundle_authoring_realtime_channels_name_template():
    content = BUNDLE_AUTHORING.read_text()
    # Channel name template uses {field_name} placeholders
    assert "{" in content and "}" in content, \
        "Missing channel name template with {field_name} placeholders"
    assert "replaced from payload" in content, \
        "Missing explanation of channel name template replacement from payload"


def test_bundle_authoring_realtime_channels_wildcard():
    content = BUNDLE_AUTHORING.read_text()
    assert "wildcard" in content.lower(), \
        "Missing wildcard explanation for event patterns"


def test_bundle_authoring_realtime_channels_auth():
    content = BUNDLE_AUTHORING.read_text()
    assert "true/false" in content or "returning true/false" in content, \
        "Missing auth interface description (returning true/false)"


def test_bundle_authoring_realtime_channels_closing():
    content = BUNDLE_AUTHORING.read_text()
    assert "No code needed in your bundle" in content, \
        "Missing closing line 'No code needed in your bundle'"


def test_bundle_authoring_agent_intents_heading():
    content = BUNDLE_AUTHORING.read_text()
    assert "### Agent Intents" in content, "Missing '### Agent Intents' heading"


def test_bundle_authoring_agent_intents_intro():
    content = BUNDLE_AUTHORING.read_text()
    assert "Define intents in your bundle for LLM-driven execution:" in content, \
        "Missing Agent Intents intro sentence"


def test_bundle_authoring_agent_intents_yaml():
    content = BUNDLE_AUTHORING.read_text()
    assert "intents:" in content, "Missing 'intents:' YAML key in BUNDLE_AUTHORING.md"


def test_bundle_authoring_agent_intents_js_example():
    content = BUNDLE_AUTHORING.read_text()
    assert "Intent" in content, "Missing Intent class reference in JS example"
    assert "Behavior" in content, "Missing Behavior class reference in JS example"
    assert "Context" in content, "Missing Context class reference in JS example"


def test_bundle_authoring_agent_intents_closing():
    content = BUNDLE_AUTHORING.read_text()
    assert "POST /api/intents/" in content, \
        "Missing 'POST /api/intents/{bundle}/{intent}' endpoint reference"
    assert "@anthropic-ai/claude-agent-sdk" in content, \
        "Missing @anthropic-ai/claude-agent-sdk requirement"
    assert "ANTHROPIC_API_KEY" in content, \
        "Missing ANTHROPIC_API_KEY requirement"


def test_bundle_authoring_embeddings_heading():
    content = BUNDLE_AUTHORING.read_text()
    assert "### Embeddings Configuration" in content, \
        "Missing '### Embeddings Configuration' heading"


def test_bundle_authoring_embeddings_intro():
    content = BUNDLE_AUTHORING.read_text()
    assert "Enable vector search in your mount plan:" in content, \
        "Missing Embeddings Configuration intro sentence"


def test_bundle_authoring_embeddings_yaml():
    content = BUNDLE_AUTHORING.read_text()
    assert "embeddings:" in content, "Missing 'embeddings:' YAML key"
    assert "provider:" in content, "Missing 'provider:' YAML key in embeddings config"
    assert "store:" in content, "Missing 'store:' YAML key in embeddings config"
    assert "local" in content, "Missing 'local' provider option"
    assert "sqlite" in content, "Missing 'sqlite' store option"


def test_bundle_authoring_code_fences_balanced():
    content = BUNDLE_AUTHORING.read_text()
    count = count_code_fences(content)
    assert count % 2 == 0, \
        f"Unbalanced code fences in BUNDLE_AUTHORING.md: {count} occurrences (must be even)"


# ──────────────────────────────────────────────────────────────────────────────
# REGISTRY.md tests
# ──────────────────────────────────────────────────────────────────────────────

def test_registry_phase3_section():
    content = REGISTRY.read_text()
    assert "Phase 3" in content, "Missing 'Phase 3' section heading in REGISTRY.md"


def test_registry_ext_embeddings():
    content = REGISTRY.read_text()
    assert "ext-embeddings" in content, "Missing 'ext-embeddings' extension in REGISTRY.md"


def test_registry_ext_otel():
    content = REGISTRY.read_text()
    assert "ext-otel" in content, "Missing 'ext-otel' extension in REGISTRY.md"


def test_registry_ext_security():
    content = REGISTRY.read_text()
    assert "ext-security" in content, "Missing 'ext-security' extension in REGISTRY.md"


def test_registry_behaviors_table_observability():
    content = REGISTRY.read_text()
    assert "observability" in content, \
        "Missing 'observability' behavior in REGISTRY.md behaviors table"


def test_registry_behaviors_table_security_hardened():
    content = REGISTRY.read_text()
    assert "security-hardened" in content, \
        "Missing 'security-hardened' behavior in REGISTRY.md behaviors table"


def test_registry_code_fences_balanced():
    content = REGISTRY.read_text()
    count = count_code_fences(content)
    assert count % 2 == 0, \
        f"Unbalanced code fences in REGISTRY.md: {count} occurrences (must be even)"


# ──────────────────────────────────────────────────────────────────────────────
# README.md tests
# ──────────────────────────────────────────────────────────────────────────────

def test_readme_agent_runtime_heading():
    content = README.read_text()
    assert "### Agent Runtime" in content, "Missing '### Agent Runtime' section in README.md"


def test_readme_agent_runtime_endpoint():
    content = README.read_text()
    assert "/api/intents/" in content, \
        "Missing /api/intents/ endpoint reference in README.md Agent Runtime section"


def test_readme_agent_runtime_claude():
    content = README.read_text()
    assert "ClaudeRuntime" in content or "claude-agent-sdk" in content, \
        "Missing ClaudeRuntime/claude-agent-sdk reference in README.md"


def test_readme_agent_runtime_manifest_features():
    content = README.read_text()
    assert "success criteria" in content or "allowed tools" in content, \
        "Missing manifest intent features (success criteria / allowed tools) in README.md"


def test_readme_observability_security_heading():
    content = README.read_text()
    assert "### Observability & Security" in content, \
        "Missing '### Observability & Security' section in README.md"


def test_readme_observability_otel():
    content = README.read_text()
    assert "OTel" in content or "OpenTelemetry" in content, \
        "Missing OTel/OpenTelemetry reference in README.md Observability section"


def test_readme_observability_rbac():
    content = README.read_text()
    assert "RBAC" in content, \
        "Missing RBAC reference in README.md Observability & Security section"


def test_readme_observability_rate_limiting():
    content = README.read_text()
    lower = content.lower()
    assert "rate limit" in lower or "rate_limit" in lower, \
        "Missing rate limiting reference in README.md Observability & Security section"


def test_readme_observability_csrf():
    content = README.read_text()
    assert "CSRF" in content, \
        "Missing CSRF reference in README.md Observability & Security section"


def test_readme_observability_audit():
    content = README.read_text()
    assert "audit" in content.lower(), \
        "Missing audit logging reference in README.md Observability & Security section"


def test_readme_code_fences_balanced():
    content = README.read_text()
    count = count_code_fences(content)
    assert count % 2 == 0, \
        f"Unbalanced code fences in README.md: {count} occurrences (must be even)"


# ──────────────────────────────────────────────────────────────────────────────
# Runner
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        # BUNDLE_AUTHORING.md
        test_bundle_authoring_realtime_channels_heading,
        test_bundle_authoring_realtime_channels_intro,
        test_bundle_authoring_realtime_channels_yaml,
        test_bundle_authoring_realtime_channels_name_template,
        test_bundle_authoring_realtime_channels_wildcard,
        test_bundle_authoring_realtime_channels_auth,
        test_bundle_authoring_realtime_channels_closing,
        test_bundle_authoring_agent_intents_heading,
        test_bundle_authoring_agent_intents_intro,
        test_bundle_authoring_agent_intents_yaml,
        test_bundle_authoring_agent_intents_js_example,
        test_bundle_authoring_agent_intents_closing,
        test_bundle_authoring_embeddings_heading,
        test_bundle_authoring_embeddings_intro,
        test_bundle_authoring_embeddings_yaml,
        test_bundle_authoring_code_fences_balanced,
        # REGISTRY.md
        test_registry_phase3_section,
        test_registry_ext_embeddings,
        test_registry_ext_otel,
        test_registry_ext_security,
        test_registry_behaviors_table_observability,
        test_registry_behaviors_table_security_hardened,
        test_registry_code_fences_balanced,
        # README.md
        test_readme_agent_runtime_heading,
        test_readme_agent_runtime_endpoint,
        test_readme_agent_runtime_claude,
        test_readme_agent_runtime_manifest_features,
        test_readme_observability_security_heading,
        test_readme_observability_otel,
        test_readme_observability_rbac,
        test_readme_observability_rate_limiting,
        test_readme_observability_csrf,
        test_readme_observability_audit,
        test_readme_code_fences_balanced,
    ]

    failed = []
    passed = []

    print("Running Phase 3 documentation tests...\n")

    for test in tests:
        try:
            test()
            passed.append(test.__name__)
            print(f"  PASS  {test.__name__}")
        except AssertionError as e:
            failed.append((test.__name__, str(e)))
            print(f"  FAIL  {test.__name__}: {e}")
        except Exception as e:
            failed.append((test.__name__, str(e)))
            print(f"  ERROR {test.__name__}: {e}")

    print(f"\n{'─' * 60}")
    print(f"Results: {len(passed)} passed, {len(failed)} failed")

    if failed:
        print("\nFailed tests:")
        for name, msg in failed:
            print(f"  - {name}: {msg}")
        sys.exit(1)
    else:
        print("\nAll tests passed!")
        sys.exit(0)
