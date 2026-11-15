"""사무실 화면(대시보드): 봇별 상태·토큰·승인 큐·최근 이벤트. FastAPI, 로컬 전용(127.0.0.1)."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

if TYPE_CHECKING:  # pragma: no cover
    from .office import Office

PAGE = """<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>사무실 화면</title>
<style>
:root{--bg:#f6f7f9;--card:#fff;--fg:#1b1f24;--muted:#6b7280;--line:#e5e7eb;--ok:#16a34a;--warn:#d97706;--bad:#dc2626}
@media(prefers-color-scheme:dark){:root{--bg:#0f1217;--card:#161b22;--fg:#e6edf3;--muted:#9da7b3;--line:#2a313b}}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,-apple-system,"Apple SD Gothic Neo","Noto Sans KR",sans-serif;padding:16px}
h1{font-size:20px;margin:0 0 12px}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:12px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px}
.name{font-weight:700;font-size:16px}.muted{color:var(--muted);font-size:13px}
.bar{height:6px;background:var(--line);border-radius:3px;margin:8px 0 4px;overflow:hidden}.bar>i{display:block;height:100%;background:var(--ok)}
.bar>i.warn{background:var(--warn)}.bar>i.bad{background:var(--bad)}
.dot{display:inline-block;width:9px;height:9px;border-radius:50%;background:var(--muted);margin-right:6px}.dot.busy{background:var(--ok)}
section{margin-top:18px}ul{margin:6px 0;padding-left:18px}li{margin:2px 0}code{font-size:12px}
</style></head><body>
<h1>🏢 사무실 화면 <span class="muted" id="ts"></span></h1>
<div class="grid" id="grid"></div>
<section><b>🔒 승인 대기</b><ul id="appr"></ul></section>
<section><b>📨 최근 넘김</b><ul id="hand"></ul></section>
<section><b>🧾 최근 이벤트</b><ul id="ev"></ul></section>
<script>
async function load(){
 const s=await (await fetch('api/status')).json();
 document.getElementById('ts').textContent=s.now;
 document.getElementById('grid').innerHTML=s.roles.map(r=>{
  const p=Math.min(100,r.budget?Math.round(r.tokens_today/r.budget*100):0);
  const cls=p>=90?'bad':p>=60?'warn':'';
  return `<div class="card"><div class="name"><span class="dot ${r.busy?'busy':''}"></span>${r.emoji} ${r.name}</div>
  <div class="muted">#${r.channel} · ${r.title}</div><div class="muted">${r.model} · effort ${r.effort}</div>
  <div class="bar"><i class="${cls}" style="width:${p}%"></i></div>
  <div class="muted">토큰 ${r.tokens_today.toLocaleString()} / ${r.budget.toLocaleString()} (${p}%)</div>
  <div class="muted">진행 ${r.running} · 완료 ${r.done} · 최근 ${r.last_activity||'-'}</div></div>`}).join('');
 document.getElementById('appr').innerHTML=s.pending_approvals.map(a=>`<li>#${a.id} ${a.role} → <code>${a.tool}</code> — ${a.summary}</li>`).join('')||'<li class="muted">없음</li>';
 document.getElementById('hand').innerHTML=s.handoffs.map(h=>`<li>${h.from_role} → ${h.to_role}: ${h.summary} <span class="muted">(끝: ${h.done_criteria||'-'})</span></li>`).join('')||'<li class="muted">없음</li>';
 document.getElementById('ev').innerHTML=s.events.map(e=>`<li><span class="muted">${e.created_at.slice(11,16)}</span> <b>${e.role}</b> ${e.kind}: ${e.detail}</li>`).join('');
}
load();setInterval(load,15000);
</script></body></html>"""


def create_app(office: Office) -> FastAPI:
    app = FastAPI(title="agent_office dashboard", version="0.1.0")

    @app.get("/", response_class=HTMLResponse)
    async def index() -> str:
        return PAGE

    @app.get("/healthz")
    async def healthz() -> dict[str, Any]:
        return {"ok": True, "roles": len(office.config.roles)}

    @app.get("/api/status")
    async def status() -> dict[str, Any]:
        from datetime import datetime

        from .heartbeat import KST

        cfg, mem = office.config, office.memory
        usage = mem.usage_by_role_today()
        roles = []
        for r in cfg.roles:
            last = mem.last_activity(r.key)
            roles.append({
                "key": r.key, "name": r.name, "title": r.title, "channel": r.channel, "emoji": r.emoji,
                "model": cfg.model_for(r), "effort": cfg.effort_for(r), "busy": office.agents[r.key].busy,
                "tokens_today": usage.get(r.key, {}).get("total", 0), "budget": cfg.budget_for(r),
                "running": len(mem.list_tasks(r.key, "running")) + len(mem.list_tasks(r.key, "awaiting_approval")),
                "done": len(mem.list_tasks(r.key, "done", limit=500)),
                "last_activity": last[11:16] if last else None,
            })
        return {
            "now": datetime.now(KST).strftime("%Y-%m-%d %H:%M KST"),
            "roles": roles,
            "pending_approvals": mem.pending_approvals(),
            "handoffs": mem.list_handoffs(limit=8),
            "events": mem.recent_events(limit=25),
        }

    @app.get("/api/tasks")
    async def tasks(role: str | None = None, status: str | None = None) -> list[dict[str, Any]]:
        return office.memory.list_tasks(role, status, limit=100)

    @app.post("/api/approvals/{approval_id}/{decision}")
    async def decide(approval_id: int, decision: str) -> dict[str, Any]:
        # 로컬 대시보드(127.0.0.1)에서만 접근 가능하므로 소유자 조작으로 본다.
        if decision not in ("approve", "deny"):
            raise HTTPException(400, "decision must be approve|deny")
        ok = office.gate.resolve(approval_id, decision == "approve")
        if not ok:
            raise HTTPException(404, "pending approval not found")
        return {"ok": True, "id": approval_id, "decision": decision}

    return app
