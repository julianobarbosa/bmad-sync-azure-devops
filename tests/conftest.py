"""Shared fixtures for BMAD sync tests."""

import os
import sys

import pytest

# Add scripts/ to path so we can import them
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))


@pytest.fixture
def tmp_file(tmp_path):
    """Helper to write content to a temp file and return its path."""
    def _write(content, filename="test.md"):
        p = tmp_path / filename
        p.write_text(content, encoding="utf-8")
        return str(p)
    return _write


@pytest.fixture
def tmp_dir(tmp_path):
    """Return a temp directory path as string."""
    return str(tmp_path)
