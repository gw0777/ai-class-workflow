"""비동기 작업 큐: 긴 논문 생성 작업을 job 으로 비동기 처리.

- 생성 요청 시 job_id 발급 → 백그라운드 실행 → 상태/결과 조회.
- HTTP 타임아웃(긴 LLM 호출) 문제를 해결한다.
- 상태는 billing 과 동일한 SQLite 파일에 저장(서버 재시작 후에도 조회 가능).
"""
from __future__ import annotations

import contextlib
import datetime
import json
import sqlite3
import uuid
from typing import Any, Optional

import billing  # DB 경로 공유


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(billing.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _now() -> str:
    return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def init_db() -> None:
    with contextlib.closing(_conn()) as c:
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                status TEXT NOT NULL,          -- queued | running | succeeded | failed
                topic TEXT,
                result TEXT,                   -- JSON (성공 시)
                error TEXT,                    -- 실패 사유
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_jobs_user ON jobs(user_id);
            """
        )
        c.commit()


def create_job(user_id: int, topic: str) -> str:
    job_id = "job_" + uuid.uuid4().hex[:16]
    now = _now()
    with contextlib.closing(_conn()) as c:
        c.execute(
            "INSERT INTO jobs(id, user_id, status, topic, created_at, updated_at) "
            "VALUES(?,?,?,?,?,?)",
            (job_id, user_id, "queued", topic, now, now),
        )
        c.commit()
    return job_id


def _update(job_id: str, **fields: Any) -> None:
    fields["updated_at"] = _now()
    cols = ", ".join(f"{k}=?" for k in fields)
    with contextlib.closing(_conn()) as c:
        c.execute(f"UPDATE jobs SET {cols} WHERE id=?", (*fields.values(), job_id))
        c.commit()


def set_running(job_id: str) -> None:
    _update(job_id, status="running")


def set_result(job_id: str, result: dict[str, Any]) -> None:
    _update(job_id, status="succeeded", result=json.dumps(result, ensure_ascii=False))


def set_error(job_id: str, message: str) -> None:
    _update(job_id, status="failed", error=message)


def get_job(job_id: str, user_id: Optional[int] = None) -> Optional[dict[str, Any]]:
    with contextlib.closing(_conn()) as c:
        row = c.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    if not row:
        return None
    if user_id is not None and row["user_id"] != user_id:
        return None  # 다른 사용자의 job 접근 차단
    d = dict(row)
    if d.get("result"):
        with contextlib.suppress(Exception):
            d["result"] = json.loads(d["result"])
    return d


def list_jobs(user_id: int, limit: int = 20) -> list[dict[str, Any]]:
    with contextlib.closing(_conn()) as c:
        rows = c.execute(
            "SELECT id, status, topic, created_at, updated_at FROM jobs "
            "WHERE user_id=? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]
