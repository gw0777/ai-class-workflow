#!/usr/bin/env python3
"""루프 스테이션 도구 — 기록 검증(validate) + 검수 보고서/대시보드 생성(build).

Python 표준 라이브러리만 사용한다. 스키마 명세는 loop-station/README.md 참조.

사용법:
    python3 loop-station/tools/loopstation.py validate [records/*.json ...]
    python3 loop-station/tools/loopstation.py build
    python3 loop-station/tools/loopstation.py new --type education --title "제목"
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path
from string import Template

BASE_DIR = Path(__file__).resolve().parent.parent  # loop-station/
RECORDS_DIR = BASE_DIR / "records"
SITE_DIR = BASE_DIR / "site"

GATE_THRESHOLD = 98
MAX_ITERATIONS = 5
ROUND1_CAP = 95
ROUND1_MIN_DEDUCTIONS = 3

RUN_ID_RE = re.compile(r"^\d{8}-\d{6}-[a-z0-9][a-z0-9-]*$")
TYPES = ("education", "html_report", "document", "general")
TYPE_LABELS = {
    "education": "교육/수업 자료",
    "html_report": "HTML 보고서",
    "document": "이메일/업무 문서",
    "general": "범용",
}
SEVERITIES = ("critical", "major", "minor")
SEVERITY_LABELS = {"critical": "치명", "major": "중대", "minor": "경미"}
VERDICTS = ("pass", "revise")


# ---------------------------------------------------------------------------
# 검증 (validate)
# ---------------------------------------------------------------------------

def validate_record(rec: dict) -> list[str]:
    """기록 dict를 검증하여 오류 메시지 목록을 반환한다. 빈 목록이면 유효."""
    errors: list[str] = []

    def err(msg: str) -> None:
        errors.append(msg)

    if not isinstance(rec, dict):
        return ["기록은 JSON 객체여야 합니다"]

    if rec.get("schema_version") != 1:
        err("schema_version은 1이어야 합니다")

    run_id = rec.get("run_id")
    if not isinstance(run_id, str) or not RUN_ID_RE.match(run_id):
        err("run_id 형식 오류: YYYYMMDD-HHMMSS-slug (영소문자/숫자/하이픈)")

    for key in ("created_at", "title", "rubric", "requirements_summary"):
        if not isinstance(rec.get(key), str) or not rec.get(key):
            err(f"{key}: 비어 있지 않은 문자열이어야 합니다")

    if rec.get("type") not in TYPES:
        err(f"type은 {TYPES} 중 하나여야 합니다")

    gate = rec.get("gate_threshold")
    if not isinstance(gate, (int, float)) or not (0 <= gate <= 100):
        err("gate_threshold는 0~100 숫자여야 합니다")
        gate = GATE_THRESHOLD

    deliverables = rec.get("deliverables")
    if not isinstance(deliverables, list) or not deliverables:
        err("deliverables는 1개 이상의 목록이어야 합니다")
    else:
        for i, d in enumerate(deliverables):
            if not isinstance(d, dict) or not all(
                isinstance(d.get(k), str) and d.get(k)
                for k in ("path", "format", "description")
            ):
                err(f"deliverables[{i}]: path/format/description 문자열 필수")

    iterations = rec.get("iterations")
    if not isinstance(iterations, list) or not iterations:
        err("iterations는 1개 이상의 목록이어야 합니다")
        iterations = []
    if len(iterations) > MAX_ITERATIONS:
        err(f"iterations는 최대 {MAX_ITERATIONS}회전입니다")

    for i, it in enumerate(iterations):
        prefix = f"iterations[{i}]"
        if not isinstance(it, dict):
            err(f"{prefix}: 객체여야 합니다")
            continue
        if it.get("round") != i + 1:
            err(f"{prefix}: round는 1부터 1씩 증가해야 합니다 (기대값 {i + 1})")
        if it.get("verdict") not in VERDICTS:
            err(f"{prefix}: verdict는 pass|revise 여야 합니다")

        criteria = it.get("criteria")
        if not isinstance(criteria, list) or not criteria:
            err(f"{prefix}: criteria는 1개 이상의 목록이어야 합니다")
            criteria = []
        score_sum = 0
        for j, c in enumerate(criteria):
            cp = f"{prefix}.criteria[{j}]"
            if not isinstance(c, dict):
                err(f"{cp}: 객체여야 합니다")
                continue
            score, mx = c.get("score"), c.get("max")
            if not isinstance(score, (int, float)) or not (0 <= score <= 5):
                err(f"{cp}: score는 0~5 숫자여야 합니다")
                score = 0
            if mx != 5:
                err(f"{cp}: max는 5여야 합니다")
            for k in ("category", "item", "comment"):
                if not isinstance(c.get(k), str) or not c.get(k):
                    err(f"{cp}: {k} 문자열 필수 (만점 항목도 코멘트 필수)")
            score_sum += score

        total = it.get("total")
        if not isinstance(total, (int, float)) or not (0 <= total <= 100):
            err(f"{prefix}: total은 0~100 숫자여야 합니다")
        elif criteria and total != score_sum:
            err(f"{prefix}: total({total})이 항목 점수 합({score_sum})과 다릅니다")

        deductions = it.get("deductions")
        if not isinstance(deductions, list):
            err(f"{prefix}: deductions는 목록이어야 합니다")
            deductions = []
        for j, d in enumerate(deductions):
            dp = f"{prefix}.deductions[{j}]"
            if not isinstance(d, dict):
                err(f"{dp}: 객체여야 합니다")
                continue
            if d.get("severity") not in SEVERITIES:
                err(f"{dp}: severity는 critical|major|minor 여야 합니다")
            pts = d.get("points")
            if not isinstance(pts, (int, float)) or pts >= 0:
                err(f"{dp}: points는 음수여야 합니다")
            for k in ("where", "reason", "fix_directive"):
                if not isinstance(d.get(k), str) or not d.get(k):
                    err(f"{dp}: {k} 문자열 필수")

        # 회전 1 무결성 규칙
        if i == 0 and isinstance(total, (int, float)) and total > ROUND1_CAP:
            err(f"{prefix}: 회전 1 총점은 {ROUND1_CAP}점 상한입니다 (채점 무결성 규칙)")
        if i == 0 and len(deductions) < ROUND1_MIN_DEDUCTIONS:
            err(f"{prefix}: 회전 1은 개선점 {ROUND1_MIN_DEDUCTIONS}건 이상 도출해야 합니다")

    final_total = rec.get("final_total")
    passed = rec.get("passed")
    if not isinstance(final_total, (int, float)):
        err("final_total은 숫자여야 합니다")
    elif iterations and isinstance(iterations[-1], dict) and \
            final_total != iterations[-1].get("total"):
        err("final_total은 마지막 회전의 total과 같아야 합니다")
    if not isinstance(passed, bool):
        err("passed는 불리언이어야 합니다")
    elif isinstance(final_total, (int, float)) and passed != (final_total >= gate):
        err(f"passed({passed})가 final_total({final_total}) >= gate({gate})와 모순됩니다")

    # 마지막 회전 verdict 일치 + 앵커 규칙
    if iterations and isinstance(iterations[-1], dict):
        last = iterations[-1]
        expected = "pass" if passed else "revise"
        if isinstance(passed, bool) and last.get("verdict") != expected:
            err(f"마지막 회전 verdict는 {expected} 여야 합니다")
        if passed is True and isinstance(last.get("deductions"), list):
            counts = {s: 0 for s in SEVERITIES}
            for d in last["deductions"]:
                if isinstance(d, dict) and d.get("severity") in counts:
                    counts[d["severity"]] += 1
            if counts["critical"] > 0 or counts["major"] > 0 or counts["minor"] > 2:
                err(
                    "앵커 규칙 위반: 통과하려면 마지막 회전이 치명 0건 + 중대 0건 + "
                    f"경미 최대 2건이어야 합니다 (현재 치명 {counts['critical']}, "
                    f"중대 {counts['major']}, 경미 {counts['minor']})"
                )

    return errors


def load_and_validate(path: Path) -> tuple[dict | None, list[str]]:
    try:
        rec = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, [f"JSON 읽기 실패: {exc}"]
    errors = validate_record(rec)
    if isinstance(rec, dict) and isinstance(rec.get("run_id"), str):
        expected_name = rec["run_id"] + ".json"
        if path.name != expected_name:
            errors.append(f"파일명은 {expected_name} 이어야 합니다 (현재 {path.name})")
    return rec, errors


# ---------------------------------------------------------------------------
# HTML 렌더링 (build)
# ---------------------------------------------------------------------------

_CSS = """\
:root { --bg:#ffffff; --fg:#1a1a1a; --muted:#5c5c5c; --line:#dcdcdc;
  --card:#f6f6f6; --accent:#2456a6; --pass:#1c7a3d; --fail:#b32424;
  --bar:#2456a6; --barbg:#e4e4e4; }
@media (prefers-color-scheme: dark) {
  :root { --bg:#16181c; --fg:#e8e8e8; --muted:#a0a0a0; --line:#3a3d44;
    --card:#20232a; --accent:#7fa7e0; --pass:#54c078; --fail:#e06c6c;
    --bar:#7fa7e0; --barbg:#33363d; } }
* { box-sizing: border-box; }
body { margin:0; padding:2rem 1rem; background:var(--bg); color:var(--fg);
  font-family:'Malgun Gothic','Apple SD Gothic Neo',sans-serif; line-height:1.6; }
main { max-width:60rem; margin:0 auto; }
h1 { font-size:1.5rem; } h2 { font-size:1.15rem; margin-top:2rem; }
a { color:var(--accent); }
table { border-collapse:collapse; width:100%; margin:0.5rem 0; }
th, td { border:1px solid var(--line); padding:0.4rem 0.6rem; text-align:left;
  font-size:0.92rem; }
th { background:var(--card); }
.tablewrap { overflow-x:auto; }
.tiles { display:flex; flex-wrap:wrap; gap:0.8rem; margin:1rem 0; }
.tile { background:var(--card); border:1px solid var(--line); border-radius:8px;
  padding:0.8rem 1.2rem; min-width:9rem; }
.tile .num { font-size:1.6rem; font-weight:bold; }
.tile .lbl { color:var(--muted); font-size:0.85rem; }
.badge { display:inline-block; padding:0.1rem 0.55rem; border-radius:999px;
  font-size:0.8rem; font-weight:bold; }
.badge.pass { background:var(--pass); color:#fff; }
.badge.fail { background:var(--fail); color:#fff; }
.bar { background:var(--barbg); border-radius:4px; height:0.6rem; width:100%;
  min-width:6rem; overflow:hidden; }
.bar > span { display:block; height:100%; background:var(--bar); }
.muted { color:var(--muted); font-size:0.88rem; }
.sev-critical { color:var(--fail); font-weight:bold; }
.sev-major { color:var(--fail); }
.sev-minor { color:var(--muted); }
footer { margin-top:3rem; color:var(--muted); font-size:0.85rem; }
"""

_PAGE = Template("""\
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>$title</title>
<style>
$css
</style>
</head>
<body>
<main>
$body
<footer>루프 스테이션 — 98점 게이트 품질 시스템 (loopstation.py build 로 생성됨)</footer>
</main>
</body>
</html>
""")


def _e(value: object) -> str:
    return html.escape(str(value), quote=True)


def _badge(passed: bool) -> str:
    return ('<span class="badge pass">통과</span>' if passed
            else '<span class="badge fail">미통과</span>')


def _score_bar(total: float) -> str:
    pct = max(0, min(100, int(round(total))))
    return (f'<div class="bar" role="img" aria-label="{pct}점">'
            f'<span style="width:{pct}%"></span></div>')


def render_run_page(rec: dict) -> str:
    it_rows = "".join(
        f"<tr><td>{_e(it['round'])}</td><td>{_e(it['total'])}/100</td>"
        f"<td>{_score_bar(it['total'])}</td>"
        f"<td>{'통과' if it['verdict'] == 'pass' else '재작업'}</td>"
        f"<td>{_e(len(it.get('deductions', [])))}건</td></tr>"
        for it in rec["iterations"]
    )

    last = rec["iterations"][-1]
    crit_rows = "".join(
        f"<tr><td>{_e(c['category'])}</td><td>{_e(c['item'])}</td>"
        f"<td>{_e(c['score'])}/{_e(c['max'])}</td><td>{_e(c['comment'])}</td></tr>"
        for c in last["criteria"]
    )

    ded_sections = []
    for it in rec["iterations"]:
        rows = "".join(
            f"<tr><td><span class=\"sev-{_e(d['severity'])}\">"
            f"{SEVERITY_LABELS.get(d['severity'], _e(d['severity']))}"
            f" ({_e(d['points'])})</span></td>"
            f"<td>{_e(d['where'])}</td><td>{_e(d['reason'])}</td>"
            f"<td>{_e(d['fix_directive'])}</td></tr>"
            for d in it.get("deductions", [])
        ) or '<tr><td colspan="4" class="muted">감점 없음</td></tr>'
        ded_sections.append(
            f"<h3>회전 {_e(it['round'])} — {_e(it['total'])}점</h3>"
            f'<div class="tablewrap"><table><tr><th>등급(감점)</th><th>위치</th>'
            f"<th>사유</th><th>수정 지시</th></tr>{rows}</table></div>"
        )

    deliv_rows = "".join(
        f"<tr><td><a href=\"../../{_e(d['path'])}\">{_e(d['path'])}</a></td>"
        f"<td>{_e(d['format'])}</td><td>{_e(d['description'])}</td></tr>"
        for d in rec["deliverables"]
    )

    body = f"""\
<p><a href="index.html">← 대시보드</a></p>
<h1>검수 보고서: {_e(rec['title'])}</h1>
<div class="tablewrap"><table>
<tr><th>run_id</th><td>{_e(rec['run_id'])}</td></tr>
<tr><th>생성 시각</th><td>{_e(rec['created_at'])}</td></tr>
<tr><th>유형</th><td>{TYPE_LABELS.get(rec['type'], _e(rec['type']))}</td></tr>
<tr><th>루브릭</th><td>{_e(rec['rubric'])}</td></tr>
<tr><th>게이트</th><td>{_e(rec['gate_threshold'])}점 이상</td></tr>
<tr><th>최종 점수</th><td>{_e(rec['final_total'])}/100 {_badge(rec['passed'])}</td></tr>
<tr><th>요구사항 요약</th><td>{_e(rec['requirements_summary'])}</td></tr>
</table></div>

<h2>회전별 점수 추이</h2>
<div class="tablewrap"><table>
<tr><th>회전</th><th>총점</th><th></th><th>판정</th><th>감점 수</th></tr>
{it_rows}</table></div>

<h2>최종 회전 항목별 점수</h2>
<div class="tablewrap"><table>
<tr><th>카테고리</th><th>하위 항목</th><th>점수</th><th>코멘트</th></tr>
{crit_rows}</table></div>

<h2>개선 이력 (회전별 감점·수정 지시)</h2>
{''.join(ded_sections)}

<h2>산출물</h2>
<div class="tablewrap"><table>
<tr><th>경로</th><th>형식</th><th>설명</th></tr>
{deliv_rows}</table></div>
"""
    if rec.get("notes"):
        body += f"<h2>비고</h2><p>{_e(rec['notes'])}</p>\n"
    return _PAGE.substitute(title=f"검수 보고서 — {_e(rec['title'])}",
                            css=_CSS, body=body)


def render_index_page(records: list[dict]) -> str:
    n = len(records)
    avg_score = round(sum(r["final_total"] for r in records) / n, 1) if n else 0
    avg_iter = round(sum(len(r["iterations"]) for r in records) / n, 1) if n else 0
    passed_n = sum(1 for r in records if r["passed"])

    type_counts: dict[str, int] = {}
    for r in records:
        type_counts[r["type"]] = type_counts.get(r["type"], 0) + 1
    type_summary = " · ".join(
        f"{TYPE_LABELS.get(t, t)} {c}건" for t, c in sorted(type_counts.items())
    ) or "—"

    rows = "".join(
        f"<tr><td><a href=\"run-{_e(r['run_id'])}.html\">{_e(r['run_id'])}</a></td>"
        f"<td>{_e(r['created_at'])}</td>"
        f"<td>{TYPE_LABELS.get(r['type'], _e(r['type']))}</td>"
        f"<td>{_e(r['title'])}</td>"
        f"<td>{_e(len(r['iterations']))}회전</td>"
        f"<td>{_e(r['final_total'])}/100</td>"
        f"<td>{_score_bar(r['final_total'])}</td>"
        f"<td>{_badge(r['passed'])}</td></tr>"
        for r in sorted(records, key=lambda r: r["run_id"], reverse=True)
    ) or '<tr><td colspan="8" class="muted">기록 없음</td></tr>'

    body = f"""\
<h1>루프 스테이션 대시보드</h1>
<p class="muted">모든 산출물은 98/100점 게이트를 통과해야 합니다. (agent.md 참조)</p>
<div class="tiles">
<div class="tile"><div class="num">{n}</div><div class="lbl">총 실행 수</div></div>
<div class="tile"><div class="num">{passed_n}</div><div class="lbl">통과 실행</div></div>
<div class="tile"><div class="num">{avg_score}</div><div class="lbl">평균 최종 점수</div></div>
<div class="tile"><div class="num">{avg_iter}</div><div class="lbl">평균 회전 수</div></div>
</div>
<p class="muted">유형별: {type_summary}</p>
<div class="tablewrap"><table>
<tr><th>run_id</th><th>일시</th><th>유형</th><th>제목</th><th>회전</th>
<th>최종 점수</th><th></th><th>판정</th></tr>
{rows}</table></div>
"""
    return _PAGE.substitute(title="루프 스테이션 대시보드", css=_CSS, body=body)


def build(records_dir: Path = RECORDS_DIR, site_dir: Path = SITE_DIR) -> list[Path]:
    """records/*.json 을 모두 검증한 뒤 site/ 에 HTML을 생성한다."""
    paths = sorted(records_dir.glob("*.json"))
    records: list[dict] = []
    failures: list[str] = []
    for p in paths:
        rec, errors = load_and_validate(p)
        if errors:
            failures.append(f"{p.name}:\n  - " + "\n  - ".join(errors))
        elif rec is not None:
            records.append(rec)
    if failures:
        raise SystemExit("기록 검증 실패 — build 중단:\n" + "\n".join(failures))

    site_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for rec in records:
        out = site_dir / f"run-{rec['run_id']}.html"
        out.write_text(render_run_page(rec), encoding="utf-8")
        written.append(out)
    index = site_dir / "index.html"
    index.write_text(render_index_page(records), encoding="utf-8")
    written.append(index)
    return written


# ---------------------------------------------------------------------------
# 스켈레톤 (new)
# ---------------------------------------------------------------------------

def skeleton(type_: str, title: str) -> dict:
    return {
        "schema_version": 1,
        "run_id": "YYYYMMDD-HHMMSS-slug",
        "created_at": "YYYY-MM-DDTHH:MM:SS+09:00",
        "type": type_,
        "title": title,
        "rubric": f"loop-station/rubrics/{type_}.md",
        "gate_threshold": GATE_THRESHOLD,
        "requirements_summary": "",
        "deliverables": [{"path": "", "format": "", "description": ""}],
        "iterations": [{
            "round": 1, "total": 0,
            "criteria": [{"category": "", "item": "", "score": 0, "max": 5,
                          "comment": ""}],
            "deductions": [{"severity": "minor", "points": -1, "where": "",
                            "reason": "", "fix_directive": ""}],
            "verdict": "revise",
        }],
        "final_total": 0,
        "passed": False,
        "notes": "",
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="루프 스테이션 도구")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_val = sub.add_parser("validate", help="기록 JSON 검증")
    p_val.add_argument("files", nargs="*", help="검증할 기록 파일 (생략 시 records/ 전체)")

    sub.add_parser("build", help="검수 보고서/대시보드 HTML 생성")

    p_new = sub.add_parser("new", help="기록 스켈레톤 JSON 출력")
    p_new.add_argument("--type", choices=TYPES, required=True)
    p_new.add_argument("--title", required=True)

    args = parser.parse_args(argv)

    if args.cmd == "validate":
        files = [Path(f) for f in args.files] or sorted(RECORDS_DIR.glob("*.json"))
        if not files:
            print("검증할 기록이 없습니다", file=sys.stderr)
            return 1
        failed = False
        for path in files:
            _, errors = load_and_validate(path)
            if errors:
                failed = True
                print(f"[실패] {path}")
                for e in errors:
                    print(f"  - {e}")
            else:
                print(f"[OK] {path}")
        return 1 if failed else 0

    if args.cmd == "build":
        written = build()
        for p in written:
            print(f"생성: {p}")
        return 0

    if args.cmd == "new":
        print(json.dumps(skeleton(args.type, args.title),
                         ensure_ascii=False, indent=2))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
