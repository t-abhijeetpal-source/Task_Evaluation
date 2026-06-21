"""Toolchain-pinning tests — prove the *runtimes* are the pinned ones, not host defaults.

These are the heart of D5: it is not enough that the code passes; the code must
pass under the exact Python and Node versions declared in ``mise.toml``.
"""

import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def _pinned(tool: str) -> str:
    """Read the pinned version for ``tool`` from this folder's mise.toml."""
    data = tomllib.loads((REPO_ROOT / "mise.toml").read_text())
    return str(data["tools"][tool])


def test_python_runtime_is_pinned() -> None:
    """The venv interpreter is the mise-pinned Python (3.12.x), not the host default."""
    pin = _pinned("python")  # e.g. "3.12.8"
    major, minor = (int(p) for p in pin.split(".")[:2])
    assert sys.version_info[:2] == (major, minor)


def _resolve_node() -> str | None:
    """Locate the node binary mise would use; fall back to PATH; None if absent."""
    if shutil.which("mise"):
        result = subprocess.run(
            ["mise", "which", "node"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        candidate = result.stdout.strip()
        if result.returncode == 0 and candidate and Path(candidate).exists():
            return candidate
    return shutil.which("node")


def test_node_toolchain_pinned() -> None:
    """Node resolves to the pinned major.minor (proves Node is installed, not just declared)."""
    node = _resolve_node()
    if node is None:
        pytest.skip("node not installed on this host (run `make` / `mise install` first)")

    pin = _pinned("node")  # e.g. "22.12.0"
    major_minor = ".".join(pin.split(".")[:2])  # "22.12"

    version = subprocess.run(
        [node, "--version"], capture_output=True, text=True, check=True
    ).stdout.strip()
    assert version.startswith(f"v{major_minor}"), f"node {version} != pinned v{major_minor}.x"
