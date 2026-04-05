"""Shared helpers for doc test suites (test_phase3_docs.py, test_phase4_docs.py).

All file reads happen once at import time so every test module that imports
this module pays the I/O cost only once per interpreter session.
"""

import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Canonical paths relative to the torque repo root
# ---------------------------------------------------------------------------
REPO = Path(__file__).parent.parent
BUNDLE_AUTHORING = REPO / "docs" / "BUNDLE_AUTHORING.md"
REGISTRY = REPO / "REGISTRY.md"
README = REPO / "README.md"

# ---------------------------------------------------------------------------
# Module-level cache — shared across all importing test modules
# ---------------------------------------------------------------------------
_CONTENT: dict[Path, str] = {
    BUNDLE_AUTHORING: BUNDLE_AUTHORING.read_text(),
    REGISTRY: REGISTRY.read_text(),
    README: README.read_text(),
}


def count_code_fences(content: str) -> int:
    """Return the number of triple-backtick occurrences in *content*."""
    return len(re.findall(r"```", content))
