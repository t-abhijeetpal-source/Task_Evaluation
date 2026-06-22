"""Unit tests for the D2 worker's processing core (DB faked)."""

from __future__ import annotations

import signal
from typing import Any

from tests.conftest import FakeConnection

import worker


def test_process_once_uppercases_and_marks_done(make_conn: Any) -> None:
    conn = make_conn([(1, "hello-d2")])
    count = worker.process_once(conn)
    assert count == 1
    # UPDATE params are (result, worker_id, job_id).
    assert conn.cur.updates == [("HELLO-D2", worker.WORKER_ID, 1)]
    assert conn.commits == 1


def test_process_once_empty_queue_returns_zero(make_conn: Any) -> None:
    conn = make_conn([])
    assert worker.process_once(conn) == 0
    assert conn.cur.updates == []
    assert conn.commits == 1  # still commits the (empty) transaction


def test_process_once_handles_a_full_batch(make_conn: Any) -> None:
    pending = [(i, f"job-{i}") for i in range(1, 6)]
    conn = make_conn(pending)
    count = worker.process_once(conn)
    assert count == 5
    assert [u[0] for u in conn.cur.updates] == ["JOB-1", "JOB-2", "JOB-3", "JOB-4", "JOB-5"]


def test_process_once_handles_empty_string_payload(make_conn: Any) -> None:
    conn = make_conn([(7, "")])
    worker.process_once(conn)
    assert conn.cur.updates == [("", worker.WORKER_ID, 7)]


def test_signal_handler_requests_graceful_shutdown(monkeypatch: Any) -> None:
    monkeypatch.setattr(worker, "_shutdown", False)
    worker._request_shutdown(signal.SIGTERM, None)
    assert worker._shutdown is True


def test_install_signal_handlers_registers_term_and_int() -> None:
    worker.install_signal_handlers()
    assert signal.getsignal(signal.SIGTERM) is worker._request_shutdown
    assert signal.getsignal(signal.SIGINT) is worker._request_shutdown


def test_main_drains_then_stops_on_shutdown(monkeypatch: Any) -> None:
    """main() processes work, then exits cleanly once shutdown is requested."""
    conn = FakeConnection([(1, "a")])

    class _ConnCtx:
        def __enter__(self) -> FakeConnection:
            return conn

        def __exit__(self, *exc: object) -> bool:
            return False

    monkeypatch.setattr(worker, "_shutdown", False)
    monkeypatch.setattr(worker.time, "sleep", lambda _s: None)
    monkeypatch.setattr(worker.psycopg, "connect", lambda *a, **k: _ConnCtx())

    calls = {"n": 0}
    real_process = worker.process_once

    def counting_process(c: Any) -> int:
        calls["n"] += 1
        result = real_process(c)
        if calls["n"] >= 2:  # after draining, ask the loop to stop
            worker._shutdown = True
        return result

    monkeypatch.setattr(worker, "process_once", counting_process)
    worker.main()
    assert worker._shutdown is True
    assert calls["n"] >= 2


def test_main_retries_on_error_then_breaks_on_shutdown(monkeypatch: Any) -> None:
    monkeypatch.setattr(worker, "_shutdown", False)
    monkeypatch.setattr(worker.time, "sleep", lambda _s: None)
    state = {"n": 0}

    def failing_connect(*a: Any, **k: Any) -> Any:
        state["n"] += 1
        if state["n"] >= 2:  # second attempt happens while shutting down → break
            worker._shutdown = True
        raise RuntimeError("db unavailable")

    monkeypatch.setattr(worker.psycopg, "connect", failing_connect)
    worker.main()
    assert state["n"] >= 2
