"""Tests for the signal-safe entrypoint argv construction.

The exec/signal behavior itself is verified in the container (CI smoke test);
here we just pin the argv built from $PORT.
"""

from app import entrypoint


def test_default_port(monkeypatch):
    monkeypatch.delenv("PORT", raising=False)
    assert entrypoint.build_argv() == [
        "uvicorn",
        "app.main:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
    ]


def test_custom_port(monkeypatch):
    monkeypatch.setenv("PORT", "9000")
    assert entrypoint.build_argv()[-1] == "9000"
    assert entrypoint.build_argv()[:4] == ["uvicorn", "app.main:app", "--host", "0.0.0.0"]
