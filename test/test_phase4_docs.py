#!/usr/bin/env python3
"""Tests for Phase 4 / task-8 documentation updates.

Verifies that BUNDLE_AUTHORING.md, REGISTRY.md, and README.md
have been updated with all task-8 deliverables:
  - Hot Reload section (BUNDLE_AUTHORING.md)
  - Integration Testing section (BUNDLE_AUTHORING.md)
  - torque dev hot-reload mention (README.md)
  - Testing & Development section with test-helpers (REGISTRY.md)

Run with: pytest torque/test/test_phase4_docs.py
"""

from doc_helpers import BUNDLE_AUTHORING, README, REGISTRY, _CONTENT


# ─────────────────────────────────────────────────────────────────────────────
# BUNDLE_AUTHORING.md — Hot Reload section (task-8 deliverable 1)
# ─────────────────────────────────────────────────────────────────────────────


def test_bundle_authoring_hot_reload_heading():
    content = _CONTENT[BUNDLE_AUTHORING]
    assert "## Hot Reload" in content, (
        "Missing '## Hot Reload' heading in BUNDLE_AUTHORING.md"
    )


def test_bundle_authoring_hot_reload_4step_heading():
    content = _CONTENT[BUNDLE_AUTHORING]
    assert "4-Step Reload Process" in content or "4-step" in content.lower(), (
        "Missing 4-step reload process description in Hot Reload section"
    )


def test_bundle_authoring_hot_reload_unload_step():
    content = _CONTENT[BUNDLE_AUTHORING]
    assert "Unload" in content, "Missing 'Unload' step in Hot Reload section"


def test_bundle_authoring_hot_reload_reimport_step():
    content = _CONTENT[BUNDLE_AUTHORING]
    assert "Re-import" in content or "re-import" in content.lower(), (
        "Missing 're-import' step in Hot Reload section"
    )


def test_bundle_authoring_hot_reload_reregister_step():
    content = _CONTENT[BUNDLE_AUTHORING]
    assert "Re-register" in content or "re-register" in content.lower(), (
        "Missing 're-register' step in Hot Reload section"
    )


def test_bundle_authoring_hot_reload_websocket_notify_step():
    content = _CONTENT[BUNDLE_AUTHORING]
    assert "WebSocket notify" in content or "WebSocket" in content, (
        "Missing 'WebSocket notify' step in Hot Reload section"
    )


def test_bundle_authoring_hot_reload_auto_reload_list():
    content = _CONTENT[BUNDLE_AUTHORING]
    assert (
        "What Reloads Automatically" in content
        or "reloads automatically" in content.lower()
    ), "Missing 'What Reloads Automatically' list in Hot Reload section"


def test_bundle_authoring_hot_reload_full_restart_list():
    content = _CONTENT[BUNDLE_AUTHORING]
    assert (
        "Full Restart" in content
        or "full restart" in content.lower()
        or "Requires a Full Restart" in content
    ), "Missing 'What Requires a Full Restart' list in Hot Reload section"


def test_bundle_authoring_hot_reload_limitations():
    content = _CONTENT[BUNDLE_AUTHORING]
    assert "Limitations" in content, (
        "Missing 'Limitations' section in Hot Reload section"
    )
    assert "300ms debounce" in content or "300ms" in content, (
        "Missing 300ms debounce limitation in Hot Reload section"
    )


def test_bundle_authoring_hot_reload_dev_only():
    content = _CONTENT[BUNDLE_AUTHORING]
    assert "Development only" in content, (
        "Missing 'Development only' limitation in Hot Reload section"
    )


def test_bundle_authoring_hot_reload_websocket_format():
    content = _CONTENT[BUNDLE_AUTHORING]
    assert "__torque_reload" in content, (
        "Missing '__torque_reload' WebSocket notification format in Hot Reload section"
    )


def test_bundle_authoring_hot_reload_websocket_json_fields():
    content = _CONTENT[BUNDLE_AUTHORING]
    # The JSON block should document type, bundle, and timestamp fields
    assert '"type"' in content and '"bundle"' in content, (
        "Missing WebSocket notification JSON fields (type, bundle, timestamp)"
    )
    assert '"timestamp"' in content, (
        "Missing 'timestamp' field in WebSocket notification format"
    )


# ─────────────────────────────────────────────────────────────────────────────
# BUNDLE_AUTHORING.md — Integration Testing section (task-8 deliverable 2)
# ─────────────────────────────────────────────────────────────────────────────


def test_bundle_authoring_integration_testing_heading():
    content = _CONTENT[BUNDLE_AUTHORING]
    assert "## Integration Testing" in content, (
        "Missing '## Integration Testing' heading in BUNDLE_AUTHORING.md"
    )


def test_bundle_authoring_integration_testing_create_test_app():
    content = _CONTENT[BUNDLE_AUTHORING]
    assert "createTestApp" in content, (
        "Missing 'createTestApp' in Integration Testing section of BUNDLE_AUTHORING.md"
    )


def test_bundle_authoring_integration_testing_test_helpers_package():
    content = _CONTENT[BUNDLE_AUTHORING]
    assert "@torquedev/test-helpers" in content, (
        "Missing '@torquedev/test-helpers' import in Integration Testing section"
    )


def test_bundle_authoring_integration_testing_setup_install():
    content = _CONTENT[BUNDLE_AUTHORING]
    assert "npm install --save-dev @torquedev/test-helpers" in content, (
        "Missing npm install --save-dev @torquedev/test-helpers setup command"
    )


def test_bundle_authoring_integration_testing_usage_example():
    content = _CONTENT[BUNDLE_AUTHORING]
    # Usage example should show before/after hooks and app.fetch
    assert "app.fetch" in content, (
        "Missing 'app.fetch' usage example in Integration Testing section"
    )
    assert "app.close" in content, "Missing 'app.close' in Integration Testing section"


def test_bundle_authoring_integration_testing_api_table():
    content = _CONTENT[BUNDLE_AUTHORING]
    # API table should have at least fetch, port, close
    assert "| Member" in content or "| Member |" in content, (
        "Missing API table header in Integration Testing section"
    )
    assert "fetch" in content and "close" in content, (
        "Missing required API table members (fetch, close)"
    )


# ─────────────────────────────────────────────────────────────────────────────
# README.md — torque dev hot reload mention (task-8 deliverable 3)
# ─────────────────────────────────────────────────────────────────────────────


def test_readme_torque_dev_hot_reload_mention():
    content = _CONTENT[README]
    # torque dev line should mention hot reload
    assert "hot reload" in content.lower(), (
        "Missing 'hot reload' mention in README.md torque dev CLI entry"
    )


def test_readme_torque_dev_command_present():
    content = _CONTENT[README]
    assert "torque dev" in content, (
        "Missing 'torque dev' command in README.md CLI section"
    )


def test_readme_test_helpers_install():
    content = _CONTENT[README]
    assert "@torquedev/test-helpers" in content, (
        "Missing '@torquedev/test-helpers' install instructions in README.md"
    )


# ─────────────────────────────────────────────────────────────────────────────
# REGISTRY.md — Testing & Development section (task-8 deliverable 4)
# ─────────────────────────────────────────────────────────────────────────────


def test_registry_testing_development_heading():
    content = _CONTENT[REGISTRY]
    assert "## Testing & Development" in content, (
        "Missing '## Testing & Development' section heading in REGISTRY.md"
    )


def test_registry_test_helpers_package():
    content = _CONTENT[REGISTRY]
    assert "@torquedev/test-helpers" in content, (
        "Missing '@torquedev/test-helpers' row in REGISTRY.md Testing section"
    )


def test_registry_test_helpers_save_dev():
    content = _CONTENT[REGISTRY]
    assert "npm install --save-dev @torquedev/test-helpers" in content, (
        "Missing '--save-dev' install command for test-helpers in REGISTRY.md"
    )


def test_registry_extensions_all_8_packages():
    content = _CONTENT[REGISTRY]
    expected_extensions = [
        "ext-authorization",
        "ext-soft-delete",
        "ext-async-events",
        "ext-search",
        "ext-storage",
        "ext-embeddings",
        "ext-otel",
        "ext-security",
    ]
    for ext in expected_extensions:
        assert ext in content, f"Missing '{ext}' in REGISTRY.md Extensions section"
