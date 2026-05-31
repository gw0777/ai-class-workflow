"""billing 모듈 단위 테스트 (네트워크/Stripe 불필요, 임시 SQLite 사용)."""
from __future__ import annotations

import os
import sys
import tempfile

# 임시 DB 경로를 import 전에 지정
_TMP_DB = os.path.join(tempfile.mkdtemp(), "billing_test.db")
os.environ["BILLING_DB"] = _TMP_DB

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import billing  # noqa: E402


def setup_module(module):  # pytest 진입 시 1회
    billing.init_db()


def test_create_user_has_key_and_free_plan():
    u = billing.create_user(email="a@example.com")
    assert u["api_key"].startswith("ppk_")
    assert billing.get_plan(u["id"]) == "free"
    assert billing.get_user_by_api_key(u["api_key"])["id"] == u["id"]


def test_free_quota_is_three_per_month():
    u = billing.create_user()
    q = billing.quota_status(u["id"])
    assert q["plan"] == "free"
    assert q["monthly_paper_limit"] == 3
    assert q["remaining"] == 3
    assert q["unlimited"] is False
    assert billing.can_generate(u["id"]) is True


def test_quota_decrements_and_blocks_after_limit():
    u = billing.create_user()
    for _ in range(3):
        assert billing.can_generate(u["id"]) is True
        billing.record_paper(u["id"], "주제")
    assert billing.count_papers_this_month(u["id"]) == 3
    assert billing.quota_status(u["id"])["remaining"] == 0
    assert billing.can_generate(u["id"]) is False  # 무료 한도 소진


def test_pro_plan_is_unlimited():
    u = billing.create_user()
    billing.set_plan(u["id"], "pro")
    for _ in range(10):
        billing.record_paper(u["id"], "주제")
    q = billing.quota_status(u["id"])
    assert q["plan"] == "pro"
    assert q["unlimited"] is True
    assert q["remaining"] is None
    assert billing.can_generate(u["id"]) is True


def test_api_call_counting_does_not_affect_paper_quota():
    u = billing.create_user()
    for _ in range(5):
        billing.record_api_call(u["id"], "/api/usage", 200)
    # api_call 은 논문 한도에 영향 없음
    assert billing.count_papers_this_month(u["id"]) == 0
    assert billing.quota_status(u["id"])["remaining"] == 3


def test_stripe_checkout_completed_upgrades_to_pro():
    u = billing.create_user()
    event = {
        "type": "checkout.session.completed",
        "data": {"object": {"client_reference_id": u["api_key"], "customer": "cus_123",
                             "subscription": "sub_123"}},
    }
    res = billing.handle_stripe_event(event)
    assert res["handled"] is True
    assert billing.get_plan(u["id"]) == "pro"


def test_stripe_subscription_deleted_downgrades_to_free():
    u = billing.create_user()
    billing.set_customer(u["id"], "cus_xyz")
    billing.set_plan(u["id"], "pro")
    event = {
        "type": "customer.subscription.deleted",
        "data": {"object": {"customer": "cus_xyz"}},
    }
    res = billing.handle_stripe_event(event)
    assert res["handled"] is True
    assert billing.get_plan(u["id"]) == "free"


def _run_all():
    setup_module(None)
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)}/{len(fns)} passed")


if __name__ == "__main__":
    _run_all()
