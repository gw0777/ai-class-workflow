"""jobs 모듈 단위 테스트 (임시 SQLite)."""
from __future__ import annotations

import os
import sys
import tempfile

os.environ["BILLING_DB"] = os.path.join(tempfile.mkdtemp(), "jobs_test.db")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import billing  # noqa: E402
import jobs  # noqa: E402


def setup_module(module):
    billing.init_db()
    jobs.init_db()


def test_create_and_get_job():
    jid = jobs.create_job(1, "주제")
    assert jid.startswith("job_")
    j = jobs.get_job(jid)
    assert j["status"] == "queued"
    assert j["topic"] == "주제"


def test_status_transitions_and_result():
    jid = jobs.create_job(1, "t")
    jobs.set_running(jid)
    assert jobs.get_job(jid)["status"] == "running"
    jobs.set_result(jid, {"passed": True, "total": 80})
    j = jobs.get_job(jid)
    assert j["status"] == "succeeded"
    assert j["result"]["total"] == 80  # JSON 역직렬화 확인


def test_error_state():
    jid = jobs.create_job(1, "t")
    jobs.set_error(jid, "boom")
    j = jobs.get_job(jid)
    assert j["status"] == "failed"
    assert j["error"] == "boom"


def test_user_isolation():
    jid = jobs.create_job(7, "t")
    assert jobs.get_job(jid, user_id=7) is not None
    assert jobs.get_job(jid, user_id=8) is None  # 다른 사용자 접근 차단


def _run_all():
    setup_module(None)
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)}/{len(fns)} passed")


if __name__ == "__main__":
    _run_all()
