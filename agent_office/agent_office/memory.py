"""SQLite 기억장치: 작업·넘김 기록·승인 큐·토큰 사용량·이벤트.

봇끼리 주고받은 정보는 채널에도 남기지만, "그때 왜 그렇게 판단했지"를 검색할 수 있도록
여기에도 같은 내용을 적는다. 표준 라이브러리 sqlite3만 사용한다.
"""
from __future__ import annotations

import json
import sqlite3
import threading
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT NOT NULL,
    channel TEXT NOT NULL,
    title TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'queued',      -- queued | running | awaiting_approval | done | failed | blocked
    done_criteria TEXT DEFAULT '',
    done_line TEXT DEFAULT '',                  -- 넘기기 전/끝낼 때 남기는 "한 일 한 줄"
    origin TEXT DEFAULT 'owner',                -- owner | handoff:<role> | heartbeat
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS handoffs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_role TEXT NOT NULL,
    to_role TEXT NOT NULL,
    task_id INTEGER,
    summary TEXT NOT NULL,
    done_line TEXT DEFAULT '',
    done_criteria TEXT DEFAULT '',
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS approvals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT NOT NULL,
    task_id INTEGER,
    tool TEXT NOT NULL,
    summary TEXT NOT NULL,
    payload TEXT DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'pending',     -- pending | approved | denied | expired
    message_id TEXT DEFAULT '',
    channel TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    resolved_at TEXT
);
CREATE TABLE IF NOT EXISTS usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT NOT NULL,
    day TEXT NOT NULL,
    model TEXT NOT NULL,
    input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    cache_read_tokens INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT NOT NULL,
    kind TEXT NOT NULL,                         -- message | tool | handoff | approval | heartbeat | error
    detail TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT NOT NULL,
    due_at TEXT NOT NULL,
    text TEXT NOT NULL,
    delivered INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS drafts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT NOT NULL,
    kind TEXT NOT NULL,                         -- email | document
    recipient TEXT DEFAULT '',
    subject TEXT DEFAULT '',
    body TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',
    created_at TEXT NOT NULL
);
"""


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


KST = timezone(timedelta(hours=9))


def _today() -> str:
    return datetime.now(KST).date().isoformat()


class Memory:
    """스레드 안전한 얇은 SQLite 래퍼."""

    def __init__(self, path: Path | str = ":memory:") -> None:
        self.path = str(path)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        with self._lock:
            self._conn.executescript(SCHEMA)
            self._conn.commit()

    # 내부 -------------------------------------------------------------
    def _exec(self, sql: str, params: tuple = ()) -> int:
        with self._lock:
            cur = self._conn.execute(sql, params)
            self._conn.commit()
            return int(cur.lastrowid or 0)

    def _rows(self, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
        with self._lock:
            return [dict(r) for r in self._conn.execute(sql, params).fetchall()]

    def _one(self, sql: str, params: tuple = ()) -> dict[str, Any] | None:
        rows = self._rows(sql, params)
        return rows[0] if rows else None

    # 작업 -------------------------------------------------------------
    def create_task(self, role: str, channel: str, title: str, done_criteria: str = "",
                    origin: str = "owner") -> int:
        now = _now()
        return self._exec(
            "INSERT INTO tasks(role, channel, title, status, done_criteria, origin, created_at, updated_at)"
            " VALUES(?,?,?,?,?,?,?,?)",
            (role, channel, title[:500], "queued", done_criteria, origin, now, now),
        )

    def update_task(self, task_id: int, **fields: Any) -> None:
        if not fields:
            return
        fields["updated_at"] = _now()
        cols = ", ".join(f"{k}=?" for k in fields)
        self._exec(f"UPDATE tasks SET {cols} WHERE id=?", (*fields.values(), task_id))

    def get_task(self, task_id: int) -> dict[str, Any] | None:
        return self._one("SELECT * FROM tasks WHERE id=?", (task_id,))

    def list_tasks(self, role: str | None = None, status: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        sql, params = "SELECT * FROM tasks WHERE 1=1", []
        if role:
            sql += " AND role=?"
            params.append(role)
        if status:
            sql += " AND status=?"
            params.append(status)
        sql += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        return self._rows(sql, tuple(params))

    # 넘김 -------------------------------------------------------------
    def log_handoff(self, from_role: str, to_role: str, task_id: int | None, summary: str,
                    done_line: str = "", done_criteria: str = "") -> int:
        return self._exec(
            "INSERT INTO handoffs(from_role, to_role, task_id, summary, done_line, done_criteria, created_at)"
            " VALUES(?,?,?,?,?,?,?)",
            (from_role, to_role, task_id, summary, done_line, done_criteria, _now()),
        )

    def list_handoffs(self, limit: int = 50) -> list[dict[str, Any]]:
        return self._rows("SELECT * FROM handoffs ORDER BY id DESC LIMIT ?", (limit,))

    # 승인 -------------------------------------------------------------
    def create_approval(self, role: str, task_id: int | None, tool: str, summary: str,
                        payload: dict[str, Any] | None = None, channel: str = "") -> int:
        return self._exec(
            "INSERT INTO approvals(role, task_id, tool, summary, payload, status, channel, created_at)"
            " VALUES(?,?,?,?,?,?,?,?)",
            (role, task_id, tool, summary, json.dumps(payload or {}, ensure_ascii=False), "pending", channel, _now()),
        )

    def set_approval_message(self, approval_id: int, message_id: str) -> None:
        self._exec("UPDATE approvals SET message_id=? WHERE id=?", (str(message_id), approval_id))

    def resolve_approval(self, approval_id: int, status: str) -> None:
        self._exec("UPDATE approvals SET status=?, resolved_at=? WHERE id=?", (status, _now(), approval_id))

    def get_approval(self, approval_id: int) -> dict[str, Any] | None:
        return self._one("SELECT * FROM approvals WHERE id=?", (approval_id,))

    def find_approval_by_message(self, message_id: str) -> dict[str, Any] | None:
        return self._one("SELECT * FROM approvals WHERE message_id=? AND status='pending'", (str(message_id),))

    def pending_approvals(self) -> list[dict[str, Any]]:
        return self._rows("SELECT * FROM approvals WHERE status='pending' ORDER BY id")

    # 사용량 -----------------------------------------------------------
    def add_usage(self, role: str, model: str, input_tokens: int, output_tokens: int,
                  cache_read_tokens: int = 0) -> None:
        self._exec(
            "INSERT INTO usage(role, day, model, input_tokens, output_tokens, cache_read_tokens, created_at)"
            " VALUES(?,?,?,?,?,?,?)",
            (role, _today(), model, int(input_tokens), int(output_tokens), int(cache_read_tokens), _now()),
        )

    def usage_today(self, role: str) -> dict[str, int]:
        row = self._one(
            "SELECT COALESCE(SUM(input_tokens),0) i, COALESCE(SUM(output_tokens),0) o,"
            " COALESCE(SUM(cache_read_tokens),0) c FROM usage WHERE role=? AND day=?",
            (role, _today()),
        ) or {"i": 0, "o": 0, "c": 0}
        return {"input": row["i"], "output": row["o"], "cache_read": row["c"], "total": row["i"] + row["o"]}

    def usage_by_role_today(self) -> dict[str, dict[str, int]]:
        out: dict[str, dict[str, int]] = {}
        for r in self._rows(
            "SELECT role, SUM(input_tokens) i, SUM(output_tokens) o, SUM(cache_read_tokens) c"
            " FROM usage WHERE day=? GROUP BY role", (_today(),)):
            out[r["role"]] = {"input": r["i"], "output": r["o"], "cache_read": r["c"], "total": r["i"] + r["o"]}
        return out

    # 이벤트 -----------------------------------------------------------
    def log_event(self, role: str, kind: str, detail: str) -> int:
        return self._exec("INSERT INTO events(role, kind, detail, created_at) VALUES(?,?,?,?)",
                          (role, kind, detail[:2000], _now()))

    def recent_events(self, limit: int = 30, role: str | None = None) -> list[dict[str, Any]]:
        if role:
            return self._rows("SELECT * FROM events WHERE role=? ORDER BY id DESC LIMIT ?", (role, limit))
        return self._rows("SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,))

    def last_activity(self, role: str) -> str | None:
        row = self._one("SELECT created_at FROM events WHERE role=? ORDER BY id DESC LIMIT 1", (role,))
        return row["created_at"] if row else None

    # 리마인더·초안 -----------------------------------------------------
    def add_reminder(self, role: str, due_at: str, text: str) -> int:
        return self._exec("INSERT INTO reminders(role, due_at, text, created_at) VALUES(?,?,?,?)",
                          (role, due_at, text, _now()))

    def due_reminders(self, now_iso: str | None = None) -> list[dict[str, Any]]:
        now_iso = now_iso or _now()
        return self._rows("SELECT * FROM reminders WHERE delivered=0 AND due_at<=? ORDER BY due_at", (now_iso,))

    def mark_reminder(self, reminder_id: int) -> None:
        self._exec("UPDATE reminders SET delivered=1 WHERE id=?", (reminder_id,))

    def add_draft(self, role: str, kind: str, body: str, recipient: str = "", subject: str = "") -> int:
        return self._exec(
            "INSERT INTO drafts(role, kind, recipient, subject, body, created_at) VALUES(?,?,?,?,?,?)",
            (role, kind, recipient, subject, body, _now()),
        )

    def list_drafts(self, limit: int = 20) -> list[dict[str, Any]]:
        return self._rows("SELECT * FROM drafts ORDER BY id DESC LIMIT ?", (limit,))

    def close(self) -> None:
        with self._lock:
            self._conn.close()
