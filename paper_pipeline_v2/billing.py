"""수익화 인프라: 구독 플랜 / 사용량 추적 / 한도 / Stripe 웹훅 (SQLite).

- 외부 의존성 없이 표준 라이브러리 sqlite3로 동작 (stripe는 웹훅에서만 지연 import).
- API 키 기반 테넌트 식별, 월간 논문 생성 한도(Free 3편/월, Pro·Enterprise 무제한).
- mcp_server.py 가 이 모듈을 사용해 인증/한도/미터링을 적용한다.
"""
from __future__ import annotations

import contextlib
import datetime
import json
import os
import secrets
import sqlite3
from typing import Any, Optional

DB_PATH = os.getenv(
    "BILLING_DB", os.path.join(os.path.dirname(os.path.abspath(__file__)), "billing.db")
)

# 플랜 카탈로그 (가격은 USD/월, monthly_paper_limit=None 은 무제한)
PLANS: dict[str, dict[str, Any]] = {
    "free": {
        "name": "Free",
        "price_usd": 0,
        "monthly_paper_limit": 3,
        "features": [
            "월 3편 논문 초안 생성",
            "DOCX 내보내기",
            "구글검색 기반 문헌 수집",
        ],
    },
    "pro": {
        "name": "Pro",
        "price_usd": 29,
        "monthly_paper_limit": None,  # 무제한
        "features": [
            "무제한 논문 초안 생성",
            "우선 처리 큐",
            "생성 이력 보관 및 재다운로드",
            "이메일 지원",
        ],
    },
    "enterprise": {
        "name": "Enterprise",
        "price_usd": None,  # 문의
        "monthly_paper_limit": None,
        "features": [
            "무제한 + 팀 좌석",
            "셌프호스트(온프레미스) 라이선스",
            "SSO / 감사로그",
            "전용 지원 및 SLA",
        ],
    },
}

DEFAULT_PLAN = "free"


def _now() -> str:
    return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def _month_key(dt: Optional[datetime.datetime] = None) -> str:
    return (dt or datetime.datetime.utcnow()).strftime("%Y-%m")


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with contextlib.closing(_conn()) as c:
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT,
                api_key TEXT UNIQUE NOT NULL,
                stripe_customer_id TEXT,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS subscriptions (
                user_id INTEGER PRIMARY KEY,
                plan TEXT NOT NULL DEFAULT 'free',
                status TEXT NOT NULL DEFAULT 'active',
                stripe_subscription_id TEXT,
                current_period_end TEXT,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS usage_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                kind TEXT NOT NULL,          -- 'paper' | 'api_call'
                ym TEXT NOT NULL,            -- 'YYYY-MM' (월간 집계용)
                detail TEXT,                 -- 경로/주제 등
                meta TEXT,                   -- JSON
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            CREATE INDEX IF NOT EXISTS idx_usage_user_month
                ON usage_events(user_id, kind, ym);
            """
        )
        c.commit()


# ---------------------------------------------------------------- users/plans
def create_user(email: Optional[str] = None, plan: str = DEFAULT_PLAN) -> dict[str, Any]:
    api_key = "ppk_" + secrets.token_urlsafe(24)
    now = _now()
    with contextlib.closing(_conn()) as c:
        cur = c.execute(
            "INSERT INTO users(email, api_key, created_at) VALUES(?,?,?)",
            (email, api_key, now),
        )
        uid = cur.lastrowid
        c.execute(
            "INSERT INTO subscriptions(user_id, plan, status, updated_at) VALUES(?,?,?,?)",
            (uid, plan, "active", now),
        )
        c.commit()
    return {"id": uid, "email": email, "api_key": api_key, "plan": plan}


def get_user_by_api_key(api_key: str) -> Optional[dict[str, Any]]:
    if not api_key:
        return None
    with contextlib.closing(_conn()) as c:
        row = c.execute(
            "SELECT id, email, api_key, stripe_customer_id FROM users WHERE api_key=?",
            (api_key,),
        ).fetchone()
        if not row:
            return None
        return dict(row)


def get_user_by_customer(customer_id: str) -> Optional[dict[str, Any]]:
    with contextlib.closing(_conn()) as c:
        row = c.execute(
            "SELECT id, email, api_key, stripe_customer_id FROM users WHERE stripe_customer_id=?",
            (customer_id,),
        ).fetchone()
        return dict(row) if row else None


def get_plan(user_id: int) -> str:
    with contextlib.closing(_conn()) as c:
        row = c.execute(
            "SELECT plan FROM subscriptions WHERE user_id=?", (user_id,)
        ).fetchone()
        return row["plan"] if row else DEFAULT_PLAN


def set_plan(
    user_id: int,
    plan: str,
    *,
    status: str = "active",
    stripe_subscription_id: Optional[str] = None,
    current_period_end: Optional[str] = None,
) -> None:
    now = _now()
    with contextlib.closing(_conn()) as c:
        c.execute(
            """
            INSERT INTO subscriptions(user_id, plan, status, stripe_subscription_id,
                                      current_period_end, updated_at)
            VALUES(?,?,?,?,?,?)
            ON CONFLICT(user_id) DO UPDATE SET
                plan=excluded.plan,
                status=excluded.status,
                stripe_subscription_id=excluded.stripe_subscription_id,
                current_period_end=excluded.current_period_end,
                updated_at=excluded.updated_at
            """,
            (user_id, plan, status, stripe_subscription_id, current_period_end, now),
        )
        c.commit()


def set_customer(user_id: int, customer_id: str) -> None:
    with contextlib.closing(_conn()) as c:
        c.execute(
            "UPDATE users SET stripe_customer_id=? WHERE id=?", (customer_id, user_id)
        )
        c.commit()


# ---------------------------------------------------------------- usage/quota
def record_paper(user_id: int, topic: str, meta: Optional[dict] = None) -> None:
    _record(user_id, "paper", topic, meta)


def record_api_call(user_id: int, path: str, status_code: int) -> None:
    _record(user_id, "api_call", path, {"status": status_code})


def _record(user_id: int, kind: str, detail: str, meta: Optional[dict]) -> None:
    with contextlib.closing(_conn()) as c:
        c.execute(
            "INSERT INTO usage_events(user_id, kind, ym, detail, meta, created_at) "
            "VALUES(?,?,?,?,?,?)",
            (user_id, kind, _month_key(), detail, json.dumps(meta or {}, ensure_ascii=False), _now()),
        )
        c.commit()


def count_papers_this_month(user_id: int) -> int:
    with contextlib.closing(_conn()) as c:
        row = c.execute(
            "SELECT COUNT(*) AS n FROM usage_events WHERE user_id=? AND kind='paper' AND ym=?",
            (user_id, _month_key()),
        ).fetchone()
        return int(row["n"])


def quota_status(user_id: int) -> dict[str, Any]:
    plan = get_plan(user_id)
    limit = PLANS.get(plan, PLANS[DEFAULT_PLAN])["monthly_paper_limit"]
    used = count_papers_this_month(user_id)
    unlimited = limit is None
    remaining = None if unlimited else max(0, limit - used)
    return {
        "plan": plan,
        "monthly_paper_limit": limit,
        "used_this_month": used,
        "remaining": remaining,
        "unlimited": unlimited,
        "month": _month_key(),
    }


def can_generate(user_id: int) -> bool:
    q = quota_status(user_id)
    return q["unlimited"] or (q["remaining"] or 0) > 0


def recent_events(user_id: int, limit: int = 20) -> list[dict[str, Any]]:
    with contextlib.closing(_conn()) as c:
        rows = c.execute(
            "SELECT kind, detail, created_at FROM usage_events WHERE user_id=? "
            "ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]


# ---------------------------------------------------------------- stripe webhook
# price_id -> plan 매핑 (환경변수로 주입; 미설정 시 product/이름 기반 추정)
def _price_to_plan(price_id: Optional[str]) -> str:
    mapping = {
        os.getenv("STRIPE_PRICE_PRO", ""): "pro",
        os.getenv("STRIPE_PRICE_ENTERPRISE", ""): "enterprise",
    }
    return mapping.get(price_id or "", "pro")


def verify_and_parse_webhook(payload: bytes, sig_header: Optional[str]) -> dict[str, Any]:
    """Stripe 서명 검증 후 이벤트 dict 반환.

    STRIPE_WEBHOOK_SECRET 와 stripe 라이브러리가 모두 있으면 서명 검증,
    아니면(개발 환경) JSON 그대로 파싱한다.
    """
    secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    if secret:
        try:
            import stripe  # 지연 import

            return stripe.Webhook.construct_event(payload, sig_header, secret)  # type: ignore
        except Exception as exc:  # noqa: BLE001
            raise ValueError(f"Stripe 서명 검증 실패: {exc}") from exc
    # 개발용: 검증 없이 파싱
    return json.loads(payload.decode("utf-8"))


def handle_stripe_event(event: dict[str, Any]) -> dict[str, Any]:
    """결제 이벤트를 받아 구독 상태를 갱신한다. (기본 구조)

    지원 이벤트:
      - checkout.session.completed : client_reference_id(=api_key)로 사용자 식별 후 Pro 활성화
      - customer.subscription.updated : 상태/플랜 갱신
      - customer.subscription.deleted : Free 로 강등
    """
    etype = event.get("type", "")
    obj = (event.get("data") or {}).get("object") or {}
    result = {"event": etype, "handled": False}

    if etype == "checkout.session.completed":
        api_key = obj.get("client_reference_id")
        customer = obj.get("customer")
        user = get_user_by_api_key(api_key) if api_key else None
        if user:
            if customer:
                set_customer(user["id"], customer)
            set_plan(user["id"], "pro", status="active",
                     stripe_subscription_id=obj.get("subscription"))
            result.update(handled=True, user_id=user["id"], plan="pro")

    elif etype == "customer.subscription.updated":
        customer = obj.get("customer")
        user = get_user_by_customer(customer) if customer else None
        if user:
            items = ((obj.get("items") or {}).get("data") or [{}])
            price_id = (items[0].get("price") or {}).get("id") if items else None
            plan = _price_to_plan(price_id)
            status = obj.get("status", "active")
            plan = plan if status in ("active", "trialing") else "free"
            set_plan(user["id"], plan, status=status,
                     stripe_subscription_id=obj.get("id"),
                     current_period_end=str(obj.get("current_period_end") or ""))
            result.update(handled=True, user_id=user["id"], plan=plan, status=status)

    elif etype == "customer.subscription.deleted":
        customer = obj.get("customer")
        user = get_user_by_customer(customer) if customer else None
        if user:
            set_plan(user["id"], "free", status="canceled")
            result.update(handled=True, user_id=user["id"], plan="free")

    return result
