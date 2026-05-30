"""Markdown(SEM 논문) -> DOCX 변환기 (한국특수체육학회지 APA 스타일).

특징
----
- 표지(title page): 제목(굵게·가운데·15pt) + 학회지명 + 생성일, 이후 페이지 나눔
- 본문 바탕체(Batang) 10pt, 섹션 제목 굵게(##=12pt, ###=11pt)
- 마크다운 표 -> 워드 표(Table Grid), 표 라벨/츠션은 표 위 좌상단 정렬
- p값 선행 0 제거 (p = 0.03 -> p = .03)
- 인라인 **굵게**, *기울임* 처리
- 국문초록 다음에 영문 Abstract 섹션 자리(placeholder) 자동 삽입(없을 때만)
- 참고문헌 섹션 항목은 내어쓰기(hanging indent) 적용

사용법
------
    python md_to_docx.py <input.md> [output.docx] [--journal "한국특수체육학회지"]
"""
from __future__ import annotations

import argparse
import os
import re
from datetime import date

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Pt

BODY_FONT = "Batang"  # 바탕체
BODY_SIZE = Pt(10)

_P_VALUE_RE = re.compile(r"([pP]\s*[<>=]\s*)0(\.\d+)")
_TOKEN_RE = re.compile(r"(\*\*.+?\*\*|\*.+?\*)")


def normalize_p(text: str) -> str:
    """APA: p값 선행 0 제거."""
    return _P_VALUE_RE.sub(r"\1\2", text or "")


def set_kor_font(run, name: str = BODY_FONT, size: Pt = BODY_SIZE) -> None:
    run.font.name = name
    run.font.size = size
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = rpr.makeelement(qn("w:rFonts"), {})
        rpr.append(rfonts)
    for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rfonts.set(qn(attr), name)


def add_inline(paragraph, text: str, *, base_bold: bool = False, base_size: Pt = BODY_SIZE) -> None:
    """**굵게**/*기울임* 토큰을 run으로 분해해 추가. p값 정규화 포함."""
    text = normalize_p(text)
    for part in _TOKEN_RE.split(text):
        if not part:
            continue
        bold, italic, chunk = base_bold, False, part
        if part.startswith("**") and part.endswith("**"):
            bold, chunk = True, part[2:-2]
        elif part.startswith("*") and part.endswith("*"):
            italic, chunk = True, part[1:-1]
        run = paragraph.add_run(chunk)
        run.bold = bold
        run.italic = italic
        set_kor_font(run, size=base_size)


def _add_table(doc, rows: list[str]) -> None:
    def cells(r: str) -> list[str]:
        return [c.strip() for c in r.strip().strip("|").split("|")]

    header = cells(rows[0])
    body = [cells(r) for r in rows[2:]]  # rows[1] = 구분선
    ncol = len(header)

    table = doc.add_table(rows=1, cols=ncol)
    table.style = "Table Grid"
    table.alignment = WD_ALIGN_PARAGRAPH.LEFT
    for j, text in enumerate(header):
        add_inline(table.rows[0].cells[j].paragraphs[0], text, base_bold=True)
    for r in body:
        cell_row = table.add_row().cells
        for j in range(ncol):
            add_inline(cell_row[j].paragraphs[0], r[j] if j < len(r) else "")


def _hanging(paragraph) -> None:
    """참고문헌 내어쓰기."""
    pf = paragraph.paragraph_format
    pf.left_indent = Pt(24)
    pf.first_line_indent = Pt(-24)


def _add_title_page(doc, title: str, journal: str) -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for _ in range(6):
        p.add_run("\n")
    add_inline(p, title, base_bold=True, base_size=Pt(15))
    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_inline(sub, f"\n\n{journal}", base_bold=True, base_size=Pt(12))
    meta = doc.add_paragraph()
    meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_inline(meta, f"\n{date.today().isoformat()} 자동 생성 초안", base_size=Pt(10))
    doc.add_page_break()


def _add_english_abstract_placeholder(doc) -> None:
    h = doc.add_paragraph()
    add_inline(h, "Abstract", base_bold=True, base_size=Pt(12))
    body = doc.add_paragraph()
    body.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_inline(
        body,
        "[영문초록(Abstract)은 국문초록을 바탕으로 추후 작성·검수가 필요합니다. "
        "투고 규정에 맞춰 150~200 단어 내외로 작성하십시오.]",
    )
    kw = doc.add_paragraph()
    add_inline(kw, "**Keywords:** [작성 필요]")


def convert(src_path: str, dst_path: str, journal: str = "한국특수체육학회지") -> dict:
    lines = open(src_path, encoding="utf-8").read().splitlines()

    doc = Document()
    normal = doc.styles["Normal"].font
    normal.name = BODY_FONT
    normal.size = BODY_SIZE
    doc.styles["Normal"].element.rPr.rFonts.set(qn("w:eastAsia"), BODY_FONT)

    # 첫 '# ' 제목 -> 표지
    title = "논문"
    start = 0
    for idx, ln in enumerate(lines):
        if ln.strip().startswith("# "):
            title = ln.strip()[2:].strip()
            start = idx + 1
            break
    _add_title_page(doc, title, journal)

    in_references = False
    english_abstract_added = False
    seen_korean_abstract = False

    i, n = start, len(lines)
    while i < n:
        line = lines[i]
        s = line.strip()

        if not s or (set(s) == {"-"} and len(s) >= 3):
            i += 1
            continue

        # 표 블록
        if s.startswith("|") and i + 1 < n and re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1]):
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append(lines[i])
                i += 1
            _add_table(doc, rows)
            continue

        # 섹션 제목
        m2 = re.match(r"^(#{2,3})\s+(.*)$", s)
        if m2:
            level, htext = len(m2.group(1)), m2.group(2)
            in_references = ("참고문헌" in htext) or ("References" in htext)
            if "국문초록" in htext or "초록" == htext:
                seen_korean_abstract = True
            p = doc.add_paragraph()
            add_inline(p, htext, base_bold=True, base_size=Pt(12 if level == 2 else 11))
            i += 1
            continue

        # 표 라벨/츠션
        if re.match(r"^\*\*Table\s", s) or (s.startswith("*") and s.endswith("*")):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            add_inline(p, s)
            i += 1
            continue

        # 인용구
        if s.startswith(">"):
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Pt(18)
            add_inline(p, s.lstrip("> ").strip())
            i += 1
            continue

        # 불릿
        if s.startswith("- "):
            p = doc.add_paragraph(style="List Bullet")
            add_inline(p, s[2:])
            i += 1
            continue

        # 일반 본문 / 참고문헌
        p = doc.add_paragraph()
        if in_references:
            _hanging(p)
            add_inline(p, s)
        else:
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            add_inline(p, s)
            if seen_korean_abstract and not english_abstract_added and s.startswith("**주제어"):
                _add_english_abstract_placeholder(doc)
                english_abstract_added = True
        i += 1

    doc.save(dst_path)
    return {
        "src": src_path,
        "dst": dst_path,
        "bytes": os.path.getsize(dst_path),
        "paragraphs": len(doc.paragraphs),
        "tables": len(doc.tables),
        "english_abstract_added": english_abstract_added,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="SEM 논문 Markdown -> DOCX 변환기")
    ap.add_argument("input", help="입력 Markdown 경로")
    ap.add_argument("output", nargs="?", help="출력 DOCX 경로(생략 시 입력명.docx)")
    ap.add_argument("--journal", default="한국특수체육학회지", help="표지에 표기할 학회지명")
    args = ap.parse_args()

    out = args.output or os.path.splitext(args.input)[0] + ".docx"
    info = convert(args.input, out, journal=args.journal)
    print("저장 완료:", info["dst"])
    print(f"  크기 {info['bytes']} bytes / 문단 {info['paragraphs']} / 표 {info['tables']} "
          f"/ 영문초록자리 {'추가' if info['english_abstract_added'] else '미추가'}")


if __name__ == "__main__":
    main()
