"""검사 결과 리포트: JSON / Markdown / HTML."""
from __future__ import annotations

import datetime
import html
import json

from .compare import CheckResult, grade

_CSS = """
body{font-family:-apple-system,"Malgun Gothic","Apple SD Gothic Neo",sans-serif;margin:0;background:#f6f7f9;color:#1d1d1f}
.wrap{max-width:1080px;margin:0 auto;padding:24px 16px}
h1{font-size:22px;margin:0 0 4px}h2{font-size:17px;margin:28px 0 10px;border-bottom:1px solid #ddd;padding-bottom:6px}
.sub{color:#666;font-size:13px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:18px 0}
.card{background:#fff;border:1px solid #e3e5e8;border-radius:10px;padding:14px}
.card .v{font-size:26px;font-weight:700}.card .k{font-size:12px;color:#666}
.g-안전{color:#1a7f37}.g-주의{color:#9a6700}.g-경고{color:#bc4c00}.g-위험{color:#cf222e}
table{border-collapse:collapse;width:100%;background:#fff;font-size:13px}
th,td{border:1px solid #e3e5e8;padding:6px 8px;text-align:left;vertical-align:top}th{background:#f0f2f5}
.sent{padding:6px 8px;margin:3px 0;border-radius:6px;line-height:1.6;font-size:14px}
.sent.exact{background:#ffe3e3;border-left:4px solid #cf222e}
.sent.similar{background:#fff3d6;border-left:4px solid #bf8700}
.sent.excluded{color:#999;background:#f0f0f0}.sent.clean{background:#fff}
.sent mark{background:#ff9f9f;padding:0 1px}
.tag{display:inline-block;font-size:11px;padding:1px 6px;border-radius:10px;background:#eee;color:#555;margin-right:6px}
details{margin-top:4px;font-size:13px}summary{cursor:pointer;color:#0969da}
.src{background:#fafafa;border:1px dashed #ccc;padding:6px 8px;margin-top:4px;border-radius:6px}
.legend span{margin-right:14px;font-size:12px}
.ok{color:#1a7f37}.warn{color:#9a6700}.bad{color:#cf222e}
"""


def to_json(res: CheckResult, indent: int = 2) -> str:
    return json.dumps(res.to_dict(), ensure_ascii=False, indent=indent)


def _mark_tokens(rep) -> str:
    """일치 구간(어절 단위)을 <mark>로 표시한 HTML."""
    words = rep.text.split()
    if not rep.match or not rep.match.blocks:
        return html.escape(rep.text)
    # tokens는 공백 분리 후 구두점만 제거하므로 split() 인덱스와 토큰 인덱스가 대체로 일치한다.
    flags = [False] * len(words)
    for a, b in rep.match.blocks:
        for i in range(a, min(b, len(words))):
            flags[i] = True
    out, i = [], 0
    while i < len(words):
        if flags[i]:
            j = i
            while j < len(words) and flags[j]:
                j += 1
            out.append("<mark>" + html.escape(" ".join(words[i:j])) + "</mark>")
            i = j
        else:
            out.append(html.escape(words[i]))
            i += 1
    return " ".join(out)


def to_html(res: CheckResult) -> str:
    g = grade(res.similarity_pct)
    e = html.escape
    parts = [f"<!doctype html><html lang='ko'><head><meta charset='utf-8'><title>유사도 검사 결과 - {e(res.title)}</title>",
             f"<meta name='viewport' content='width=device-width,initial-scale=1'><style>{_CSS}</style></head><body><div class='wrap'>",
             f"<h1>유사도 검사 결과</h1><div class='sub'>{e(res.title)} &middot; {e(res.target)} &middot; "
             f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}</div>"]
    parts.append("<div class='cards'>")
    parts.append(f"<div class='card'><div class='v g-{g}'>{res.similarity_pct}%</div><div class='k'>표절률(의심문장 어절 기준) · {g}</div></div>")
    parts.append(f"<div class='card'><div class='v'>{res.exact_pct}%</div><div class='k'>정확일치율({res.config.get('min_run')}어절 이상 연속)</div></div>")
    parts.append(f"<div class='card'><div class='v'>{res.suspect_sentences}/{res.n_checked}</div><div class='k'>의심 문장 / 검사 문장 ({res.sentence_pct}%)</div></div>")
    parts.append(f"<div class='card'><div class='v'>{len(res.sources)}</div><div class='k'>일치 출처 수</div></div>")
    parts.append(f"<div class='card'><div class='v'>{res.n_excluded}</div><div class='k'>제외 문장(인용·출처·목차 등)</div></div>")
    parts.append(f"<div class='card'><div class='v'>{res.corpus_stats.get('documents', 0)}</div><div class='k'>비교 문헌 수(코퍼스)</div></div>")
    parts.append("</div>")
    if res.corpus_overlap_pct >= 60:
        parts.append(f"<p class='bad'><b>중복 문서 의심:</b> 이 문서 지문의 {res.corpus_overlap_pct}%가 이미 코퍼스에 존재합니다.</p>")
    for w in res.warnings:
        parts.append(f"<p class='warn'>⚠ {e(w)}</p>")

    parts.append("<h2>출처별 일치 현황</h2>")
    if res.sources:
        parts.append("<table><tr><th>#</th><th>출처</th><th>제목</th><th>일치 문장</th><th>어절</th><th>비율</th></tr>")
        for i, s in enumerate(res.sources, 1):
            parts.append(f"<tr><td>{i}</td><td>{e(s.source)}</td><td>{e(s.title)}</td><td>{s.n_sentences}</td><td>{s.suspect_tokens}</td><td>{s.share_pct}%</td></tr>")
        parts.append("</table>")
    else:
        parts.append("<p class='ok'>일치하는 출처가 없습니다.</p>")

    if res.references is not None:
        parts.append("<h2>참고문헌 실존 검증</h2>")
        if res.references:
            parts.append("<table><tr><th>#</th><th>참고문헌</th><th>판정</th><th>확인 제목 / DOI</th></tr>")
            for i, r in enumerate(res.references, 1):
                cls = {"확인": "ok", "의심": "warn", "미확인": "bad"}.get(r.get("status", ""), "")
                link = r.get("url") or (f"https://doi.org/{r['doi']}" if r.get("doi") else "")
                found = e(r.get("matched_title") or "")
                if link:
                    found += f" <a href='{e(link)}'>↗</a>"
                parts.append(f"<tr><td>{i}</td><td>{e(r.get('raw',''))}</td><td class='{cls}'>{e(r.get('status',''))}"
                             f"<br><span class='sub'>{e(r.get('note',''))}</span></td><td>{found}</td></tr>")
            parts.append("</table>")
        else:
            parts.append("<p>참고문헌 목록을 찾지 못했습니다.</p>")

    if res.existence is not None:
        ex = res.existence
        parts.append("<h2>기존 문헌 유무(온라인)</h2>")
        parts.append(f"<p>검색 제목: <b>{e(ex.get('title',''))}</b></p>")
        hits = ex.get("hits") or []
        if hits:
            parts.append("<table><tr><th>출처</th><th>제목</th><th>유사도</th><th>링크</th></tr>")
            for h in hits:
                parts.append(f"<tr><td>{e(h.get('provider',''))}</td><td>{e(h.get('title',''))}</td><td>{h.get('score','')}</td>"
                             f"<td><a href='{e(h.get('url',''))}'>{e(h.get('url',''))}</a></td></tr>")
            parts.append("</table>")
        else:
            parts.append("<p class='ok'>제목이 유사한 기존 문헌을 찾지 못했습니다.</p>")
        for er in ex.get("errors", []):
            parts.append(f"<p class='warn'>⚠ {e(er)}</p>")

    parts.append("<h2>본문 검사 결과</h2><p class='legend'><span class='bad'>■ 일치(연속 어절)</span><span class='warn'>■ 유사(바꿔쓰기 의심)</span><span style='color:#999'>■ 제외</span></p>")
    for rep in res.sentences:
        if rep.excluded:
            parts.append(f"<div class='sent excluded'><span class='tag'>{e(rep.excluded)}</span>{e(rep.text)}</div>")
        elif rep.match:
            m = rep.match
            cls = "exact" if m.kind == "일치" else "similar"
            parts.append(f"<div class='sent {cls}'><span class='tag'>{m.kind} · 연속 {m.longest_run}어절 · 유사도 {m.ratio}</span>{_mark_tokens(rep)}"
                         f"<details><summary>출처: {e(m.source_title or m.source)} (문장 {m.source_sent_idx + 1})</summary>"
                         f"<div class='src'>{e(m.source_text)}<div class='sub'>{e(m.source)}</div></div></details></div>")
        else:
            parts.append(f"<div class='sent clean'>{e(rep.text)}</div>")

    parts.append("<h2>검사 설정</h2><table>")
    for k, v in res.config.items():
        parts.append(f"<tr><th>{e(str(k))}</th><td>{e(str(v))}</td></tr>")
    parts.append("</table></div></body></html>")
    return "\n".join(parts)


def to_markdown(res: CheckResult, max_sentences: int = 200) -> str:
    g = grade(res.similarity_pct)
    out = [f"# 유사도 검사 결과: {res.title}", "",
           f"- 대상: `{res.target}`",
           f"- **표절률: {res.similarity_pct}% ({g})** · 정확일치율 {res.exact_pct}% · 의심 문장 {res.suspect_sentences}/{res.n_checked} ({res.sentence_pct}%)",
           f"- 제외 문장 {res.n_excluded} ({', '.join(f'{k} {v}' for k, v in res.excluded_counts.items()) or '없음'})",
           f"- 비교 문헌 {res.corpus_stats.get('documents', 0)}건 / 코퍼스 중복도 {res.corpus_overlap_pct}%", ""]
    for w in res.warnings:
        out.append(f"> ⚠ {w}")
    out += ["", "## 출처별 일치 현황", ""]
    if res.sources:
        out += ["| # | 출처 | 제목 | 일치 문장 | 어절 | 비율 |", "|---|---|---|---|---|---|"]
        out += [f"| {i} | {s.source} | {s.title} | {s.n_sentences} | {s.suspect_tokens} | {s.share_pct}% |" for i, s in enumerate(res.sources, 1)]
    else:
        out.append("일치하는 출처가 없습니다.")
    if res.references is not None:
        out += ["", "## 참고문헌 실존 검증", ""]
        if res.references:
            out += ["| # | 참고문헌 | 판정 | 비고 |", "|---|---|---|---|"]
            out += [f"| {i} | {r.get('raw','')[:120]} | {r.get('status','')} | {r.get('note','')} {('https://doi.org/' + r['doi']) if r.get('doi') else ''} |"
                    for i, r in enumerate(res.references, 1)]
        else:
            out.append("참고문헌 목록을 찾지 못했습니다.")
    if res.existence is not None:
        out += ["", "## 기존 문헌 유무(온라인)", "", f"검색 제목: **{res.existence.get('title','')}**", ""]
        hits = res.existence.get("hits") or []
        out += [f"- [{h.get('provider')}] {h.get('title')} (유사도 {h.get('score')}) {h.get('url','')}" for h in hits] or ["- 유사 제목의 기존 문헌 없음"]
        out += [f"- ⚠ {er}" for er in res.existence.get("errors", [])]
    out += ["", "## 의심 문장", ""]
    shown = 0
    for rep in res.sentences:
        if rep.match and shown < max_sentences:
            m = rep.match
            out.append(f"- **[{m.kind} · {m.longest_run}어절 · {m.ratio}]** {rep.text}")
            out.append(f"  - 출처: {m.source_title or m.source} — {m.source_text}")
            shown += 1
    if shown == 0:
        out.append("의심 문장이 없습니다.")
    return "\n".join(out) + "\n"
