"""명령행 인터페이스.

    python -m similarity_checker index add <파일|폴더>...        코퍼스에 문헌 추가
    python -m similarity_checker index add-github owner/repo     GitHub 저장소 문서 수집
    python -m similarity_checker index list | stats | remove ID
    python -m similarity_checker check <파일> [--html r.html] [--refs --online] [--exists]
    python -m similarity_checker compare <A> <B>                 1:1 비교
    python -m similarity_checker refs <파일> [--online]           참고문헌 실존 검증
    python -m similarity_checker exists <파일|--title ...>        기존 문헌 유무
    python -m similarity_checker extract <파일>                   텍스트 추출 확인
"""
from __future__ import annotations

import argparse
import json
import os
import sys

from . import __version__
from .compare import CheckResult, check_text, compare_texts, grade
from .config import CheckConfig, default_db_path
from .extract import extract, iter_files
from .index import CorpusIndex


def _cfg_from_args(a: argparse.Namespace) -> CheckConfig:
    cfg = CheckConfig()
    for k in ("min_run", "sim_threshold", "candidates", "min_tokens"):
        v = getattr(a, k, None)
        if v is not None:
            setattr(cfg, k, v)
    if getattr(a, "strict", False):
        cfg.loose = False
    if getattr(a, "no_exclude_quotes", False):
        cfg.exclude_quotes = False
    if getattr(a, "no_exclude_citations", False):
        cfg.exclude_citations = False
    if getattr(a, "no_exclude_references", False):
        cfg.exclude_references = False
    if getattr(a, "no_exclude_toc", False):
        cfg.exclude_toc = False
    cfg.exclude_sources = list(getattr(a, "exclude_source", None) or [])
    return cfg


def _add_check_opts(p: argparse.ArgumentParser) -> None:
    g = p.add_argument_group("검사 설정(카피킬러 대응)")
    g.add_argument("--min-run", type=int, help="연속 일치 어절 기준(기본 6)")
    g.add_argument("--sim-threshold", type=float, help="유사 문장 판정 임계값 0~1(기본 0.7)")
    g.add_argument("--candidates", type=int, help="문장당 정밀 비교 후보 수(기본 30)")
    g.add_argument("--min-tokens", type=int, help="검사 최소 어절 수(기본 5)")
    g.add_argument("--strict", action="store_true", help="조사/어미 제거 없이 원문 어절 그대로 비교")
    g.add_argument("--no-exclude-quotes", action="store_true", help="인용문 제외 안 함")
    g.add_argument("--no-exclude-citations", action="store_true", help="출처표시 문장 제외 안 함")
    g.add_argument("--no-exclude-references", action="store_true", help="참고문헌 목록 제외 안 함")
    g.add_argument("--no-exclude-toc", action="store_true", help="목차 제외 안 함")
    g.add_argument("--exclude-source", action="append", metavar="SUBSTR", help="출처 라벨에 포함되면 비교 제외(반복 가능)")


def _add_output_opts(p: argparse.ArgumentParser) -> None:
    g = p.add_argument_group("출력")
    g.add_argument("--html", metavar="PATH", help="HTML 리포트 저장 경로")
    g.add_argument("--json", metavar="PATH", help="JSON 결과 저장 경로")
    g.add_argument("--md", metavar="PATH", help="Markdown 리포트 저장 경로")
    g.add_argument("--out-dir", metavar="DIR", help="지정 시 html/json/md 세 가지를 모두 이 폴더에 저장")
    g.add_argument("--quiet", "-q", action="store_true")


def _write_outputs(res: CheckResult, a: argparse.Namespace, stem: str) -> list[str]:
    from .report import to_html, to_json, to_markdown

    written = []
    html_p, json_p, md_p = a.html, a.json, a.md
    if a.out_dir:
        os.makedirs(a.out_dir, exist_ok=True)
        html_p = html_p or os.path.join(a.out_dir, f"{stem}.html")
        json_p = json_p or os.path.join(a.out_dir, f"{stem}.json")
        md_p = md_p or os.path.join(a.out_dir, f"{stem}.md")
    for path, fn in ((html_p, to_html), (json_p, to_json), (md_p, to_markdown)):
        if path:
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(fn(res))
            written.append(path)
    return written


def _print_summary(res: CheckResult) -> None:
    print(f"\n=== 유사도 검사 결과: {res.title} ===")
    print(f"표절률(의심문장 어절 기준): {res.similarity_pct}%  [{grade(res.similarity_pct)}]")
    print(f"정확일치율({res.config['min_run']}어절 이상 연속): {res.exact_pct}%")
    print(f"의심 문장: {res.suspect_sentences}/{res.n_checked} ({res.sentence_pct}%)  제외 문장: {res.n_excluded} {res.excluded_counts or ''}")
    print(f"비교 문헌: {res.corpus_stats.get('documents', 0)}건  코퍼스 중복도: {res.corpus_overlap_pct}%")
    for w in res.warnings:
        print(f"  ! {w}")
    if res.sources:
        print("\n출처별 일치:")
        for i, s in enumerate(res.sources[:10], 1):
            print(f"  {i}. {s.share_pct:5.1f}%  {s.n_sentences:3d}문장  {s.title or s.source}  <{s.source}>")
    if res.references is not None:
        from .references import summarize

        print(f"\n참고문헌 검증: {summarize(res.references)}")
        for i, r in enumerate(res.references, 1):
            if r["status"] != "확인":
                print(f"  [{r['status']}] {i}. {r['raw'][:90]} — {r['note']}")
    if res.existence is not None:
        ex = res.existence
        print(f"\n기존 문헌 유무: {ex['verdict']}")
        for h in ex["hits"][:5]:
            print(f"  - [{h['provider']}] {h['title']} ({h.get('score')}) {h.get('url','')}")
        for er in ex["errors"]:
            print(f"  ! {er}")


# --------------------------------------------------------------------------- #
# 하위 명령
# --------------------------------------------------------------------------- #
def cmd_index(a: argparse.Namespace) -> int:
    idx = CorpusIndex(a.db, ngram=a.ngram or 3)
    try:
        if a.index_cmd == "add":
            files = iter_files(a.paths)
            if not files:
                print("추가할 파일이 없습니다.", file=sys.stderr)
                return 1
            for f in files:
                try:
                    doc = extract(f)
                except Exception as e:
                    print(f"  skip  {f}: {e}")
                    continue
                if doc.needs_ocr:
                    print(f"  skip  {f}: 텍스트 없음(스캔본). OCR 필요")
                    continue
                label = a.label or os.path.abspath(f)
                if a.label and len(files) > 1:
                    label = f"{a.label}/{os.path.basename(f)}"
                rec, status = idx.add_text(doc.text, source=label, title=doc.title, kind=doc.kind,
                                           meta={"path": os.path.abspath(f), "method": doc.method, "pages": doc.pages},
                                           replace=not a.no_replace)
                print(f"  {status:18s} id={rec.id:<4d} {rec.n_sentences:5d}문장  {doc.title[:60]}  <{f}>")
        elif a.index_cmd == "add-github":
            from .github_source import fetch_repo_documents

            n = 0
            for label, title, text, kind, warns in fetch_repo_documents(a.repo, token=a.token):
                if len(text.strip()) < 50:
                    print(f"  skip  {label}: 텍스트 없음")
                    continue
                rec, status = idx.add_text(text, source=label, title=title, kind=kind, replace=not a.no_replace)
                print(f"  {status:18s} id={rec.id:<4d} {rec.n_sentences:5d}문장  {title[:60]}  <{label}>")
                n += 1
            print(f"{n}개 문서 처리")
        elif a.index_cmd == "add-text":
            text = sys.stdin.read()
            rec, status = idx.add_text(text, source=a.label, title=a.title or a.label, kind="txt")
            print(f"  {status} id={rec.id} {rec.n_sentences}문장")
        elif a.index_cmd == "list":
            for d in idx.list():
                print(f"{d.id:4d}  {d.added_at}  {d.n_sentences:5d}문장 {d.n_tokens:7d}어절  {d.title[:50]:50s}  {d.source}")
            print(f"총 {len(idx.list())}건")
        elif a.index_cmd == "remove":
            for i in a.ids:
                print(f"  id={i}: {'삭제' if idx.remove(i) else '없음'}")
        elif a.index_cmd == "stats":
            print(json.dumps(idx.stats(), ensure_ascii=False, indent=2))
        return 0
    finally:
        idx.close()


def _load_target(path: str):
    doc = extract(path)
    if doc.needs_ocr:
        print(f"경고: {path} 에서 텍스트를 거의 추출하지 못했습니다(스캔본?). {doc.warnings}", file=sys.stderr)
    for w in doc.warnings:
        if "실패" in w:
            print(f"  (추출기 {w})", file=sys.stderr)
    return doc


def _attach_refs_and_exists(res: CheckResult, text: str, a: argparse.Namespace) -> None:
    if getattr(a, "refs", False):
        from .references import extract_references, verify_all

        refs = extract_references(text)
        res.references = verify_all(refs, online=a.online)
    if getattr(a, "exists", False):
        from .online import check_existence, pick_sample_sentences
        from .textproc import split_sentences

        title = a.title or res.title
        res.existence = check_existence(title, pick_sample_sentences(split_sentences(text)),
                                        github_phrases=a.github_phrases or 0)


def cmd_check(a: argparse.Namespace) -> int:
    cfg = _cfg_from_args(a)
    doc = _load_target(a.file)
    idx = CorpusIndex(a.db, ngram=cfg.index_ngram)
    try:
        for w in idx.warnings:
            print(f"경고: {w}", file=sys.stderr)
        if idx.stats()["documents"] == 0:
            print(f"경고: 코퍼스({a.db})가 비어 있습니다. 먼저 `index add` 로 비교 문헌을 넣으세요.", file=sys.stderr)
        res = check_text(doc.text, idx, cfg, target=a.file, title=a.title or doc.title)
    finally:
        idx.close()
    _attach_refs_and_exists(res, doc.text, a)
    stem = os.path.splitext(os.path.basename(a.file))[0] + "_report"
    written = _write_outputs(res, a, stem)
    if not a.quiet:
        _print_summary(res)
    for w in written:
        print(f"저장: {w}")
    if a.fail_above is not None and res.similarity_pct > a.fail_above:
        print(f"기준 초과: {res.similarity_pct}% > {a.fail_above}%", file=sys.stderr)
        return 2
    return 0


def cmd_compare(a: argparse.Namespace) -> int:
    cfg = _cfg_from_args(a)
    da, db = _load_target(a.file_a), _load_target(a.file_b)
    res = compare_texts(da.text, db.text, cfg, label_a=a.file_a, label_b=a.file_b, title_a=da.title, title_b=db.title)
    stem = os.path.splitext(os.path.basename(a.file_a))[0] + "_vs_" + os.path.splitext(os.path.basename(a.file_b))[0]
    written = _write_outputs(res, a, stem)
    if not a.quiet:
        _print_summary(res)
    for w in written:
        print(f"저장: {w}")
    return 0


def cmd_refs(a: argparse.Namespace) -> int:
    from .references import extract_references, summarize, verify_all

    doc = _load_target(a.file)
    refs = extract_references(doc.text)
    if not refs:
        print("참고문헌 목록을 찾지 못했습니다('참고문헌'/'References' 표제가 필요).")
        return 1
    results = verify_all(refs, online=a.online)
    for i, r in enumerate(results, 1):
        print(f"[{r['status']:3s}] {i:3d}. {r['raw'][:100]}")
        if r["title"]:
            print(f"         제목: {r['title'][:90]}  ({r['year']})")
        if r["note"]:
            print(f"         {r['note']}" + (f"  https://doi.org/{r['doi']}" if r.get("doi") else ""))
    print(json.dumps(summarize(results), ensure_ascii=False))
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"저장: {a.json}")
    return 0


def cmd_exists(a: argparse.Namespace) -> int:
    from .online import check_existence, pick_sample_sentences
    from .textproc import split_sentences

    title, samples = a.title, []
    if a.file:
        doc = _load_target(a.file)
        title = title or doc.title
        samples = pick_sample_sentences(split_sentences(doc.text))
    if not title:
        print("--title 또는 파일이 필요합니다.", file=sys.stderr)
        return 1
    # 로컬 코퍼스 제목 검색
    if os.path.exists(a.db):
        idx = CorpusIndex(a.db)
        local = idx.search_title(title)
        idx.close()
        if local:
            print("로컬 코퍼스 유사 제목:")
            for d, sc in local[:5]:
                print(f"  - ({sc:.2f}) {d.title}  <{d.source}>")
    res = check_existence(title, samples, github_phrases=a.github_phrases or 0)
    print(f"온라인: {res['verdict']}")
    for h in res["hits"]:
        print(f"  - [{h['provider']}] {h['title']} ({h.get('score')}) {h.get('year','')} {h.get('url','')}")
    for er in res["errors"]:
        print(f"  ! {er}")
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=2)
    return 0


def cmd_extract(a: argparse.Namespace) -> int:
    doc = extract(a.file)
    print(f"# {doc.title}  [{doc.kind}/{doc.method}, pages={doc.pages}, chars={len(doc.text)}]", file=sys.stderr)
    for w in doc.warnings:
        print(f"# {w}", file=sys.stderr)
    if a.sentences:
        from .textproc import split_sentences

        for i, s in enumerate(split_sentences(doc.text), 1):
            print(f"{i:5d}  {s}")
    else:
        print(doc.text)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="similarity_checker", description="개인용 논문 유사도·표절 검사 도구(카피킬러 대체)")
    p.add_argument("--version", action="version", version=__version__)
    p.add_argument("--db", default=default_db_path(), help=f"코퍼스 DB 경로(기본 {default_db_path()}; 환경변수 SIMCHECK_DB)")
    sub = p.add_subparsers(dest="cmd", required=True)

    pi = sub.add_parser("index", help="코퍼스 관리")
    pi.add_argument("--ngram", type=int, help="새 DB 생성 시 역색인 n-gram(기본 3)")
    si = pi.add_subparsers(dest="index_cmd", required=True)
    s = si.add_parser("add", help="파일/폴더 추가"); s.add_argument("paths", nargs="+"); s.add_argument("--label", help="출처 라벨"); s.add_argument("--no-replace", action="store_true")
    s = si.add_parser("add-github", help="GitHub 저장소 문서 수집(owner/repo[@ref][:path])"); s.add_argument("repo"); s.add_argument("--token", help="GitHub 토큰(기본 GITHUB_TOKEN)"); s.add_argument("--no-replace", action="store_true")
    s = si.add_parser("add-text", help="표준입력 텍스트 추가"); s.add_argument("--label", required=True); s.add_argument("--title")
    si.add_parser("list"); si.add_parser("stats")
    s = si.add_parser("remove"); s.add_argument("ids", type=int, nargs="+")
    pi.set_defaults(func=cmd_index)

    pc = sub.add_parser("check", help="코퍼스 대비 유사도 검사(1:N)")
    pc.add_argument("file"); pc.add_argument("--title", help="문서 제목(미지정 시 첫 줄)")
    pc.add_argument("--refs", action="store_true", help="참고문헌 실존 검증 포함")
    pc.add_argument("--exists", action="store_true", help="기존 문헌 유무(온라인) 검사 포함")
    pc.add_argument("--online", action="store_true", help="참고문헌 검증 시 Crossref/OpenAlex 조회")
    pc.add_argument("--github-phrases", type=int, help="대표 문장 N개를 GitHub 코드검색(GITHUB_TOKEN 필요)")
    pc.add_argument("--fail-above", type=float, metavar="PCT", help="표절률이 이 값을 넘으면 종료코드 2(CI용)")
    _add_check_opts(pc); _add_output_opts(pc); pc.set_defaults(func=cmd_check)

    pp = sub.add_parser("compare", help="두 문서 1:1 비교")
    pp.add_argument("file_a"); pp.add_argument("file_b")
    _add_check_opts(pp); _add_output_opts(pp); pp.set_defaults(func=cmd_compare)

    pr = sub.add_parser("refs", help="참고문헌 파싱 + 실존 검증")
    pr.add_argument("file"); pr.add_argument("--online", action="store_true"); pr.add_argument("--json")
    pr.set_defaults(func=cmd_refs)

    pe = sub.add_parser("exists", help="기존 문헌 유무 검사(제목 기준, 로컬+온라인)")
    pe.add_argument("file", nargs="?"); pe.add_argument("--title"); pe.add_argument("--github-phrases", type=int); pe.add_argument("--json")
    pe.set_defaults(func=cmd_exists)

    px = sub.add_parser("extract", help="텍스트 추출 결과 확인")
    px.add_argument("file"); px.add_argument("--sentences", action="store_true", help="문장 분리 결과로 출력")
    px.set_defaults(func=cmd_extract)
    return p


def main(argv: list[str] | None = None) -> int:
    a = build_parser().parse_args(argv)
    return a.func(a)
