"""특수체육 시각장애 교재(index.html) 정적 검사.

표준 라이브러리만 씁니다. 저장소 루트에서 실행:
    python3 -m unittest discover -s special_pe_visual_impairment/tests -v
"""
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

HTML_PATH = Path(__file__).resolve().parents[1] / "index.html"
README_PATH = Path(__file__).resolve().parents[1] / "README.md"
# 금지 용어(용어는 「특수체육」으로 통일). 소스에 그 용어가 글자 그대로 남지 않도록 유니코드 이스케이프로 적는다.
BANNED_KO = re.compile("적응\\s*(체육|신체\\s*활동|스포츠)")
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
FRAG_START = "<!-- 아티팩트 본문 시작"
FRAG_END = "<!-- 아티팩트 본문 끝 -->"
SIX_STEPS = ["전시 과제 복습", "새로운 과제 제시", "초기 과제 연습", "피드백 및 교정", "독자적인 연습", "본시 복습"]


class Node:
    def __init__(self, tag, attrs, parent, pos):
        self.tag = tag
        self.attrs = dict(attrs)
        self.parent = parent
        self.children = []
        self.pos = pos

    @property
    def classes(self):
        return set((self.attrs.get("class") or "").split())

    def text(self):
        out = []

        def walk(n):
            for c in n.children:
                if isinstance(c, str):
                    out.append(c)
                else:
                    walk(c)

        walk(self)
        return "".join(out)

    def iter(self):
        for c in self.children:
            if isinstance(c, Node):
                yield c
                yield from c.iter()

    def find_all(self, pred):
        return [n for n in self.iter() if pred(n)]

    def ancestors(self):
        p = self.parent
        while p is not None:
            yield p
            p = p.parent

    def closest(self, pred):
        for a in self.ancestors():
            if pred(a):
                return a
        return None


class TreeBuilder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#root", [], None, (0, 0))
        self.cur = self.root
        self.errors = []

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs, self.cur, self.getpos())
        self.cur.children.append(node)
        if tag not in VOID:
            self.cur = node

    def handle_startendtag(self, tag, attrs):
        self.cur.children.append(Node(tag, attrs, self.cur, self.getpos()))

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        n = self.cur
        while n is not None and n.tag != tag:
            n = n.parent
        if n is None:
            self.errors.append(f"짝 없는 </{tag}> (줄 {self.getpos()[0]})")
            return
        if n is not self.cur:
            self.errors.append(f"</{tag}> 때문에 <{self.cur.tag}>가 닫히지 않은 채 끝남 (줄 {self.getpos()[0]})")
        self.cur = n.parent

    def handle_data(self, data):
        self.cur.children.append(data)


def is_section_ch(n):
    return n.tag == "section" and "ch" in n.classes


def css_tokens(block):
    return dict(re.findall(r"(--[\w-]+)\s*:\s*([^;}]+)", block))


class TextbookStaticTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src = HTML_PATH.read_text(encoding="utf-8")
        tb = TreeBuilder()
        tb.feed(cls.src)
        tb.close()
        cls.parse_errors = tb.errors
        cls.root = tb.root
        cls.nodes = list(tb.root.iter())
        cls.by_id, cls.dup_ids = {}, []
        for n in cls.nodes:
            i = n.attrs.get("id")
            if i is None:
                continue
            if i in cls.by_id:
                cls.dup_ids.append(i)
            cls.by_id[i] = n
        cls.sections = [n for n in cls.nodes if is_section_ch(n)]
        cls.cards = [n for n in cls.nodes if n.tag == "details" and "fc" in n.classes]

    # 구조 ---------------------------------------------------------------
    def test_html_is_well_formed(self):
        self.assertEqual(self.parse_errors, [])

    def test_ids_are_unique(self):
        self.assertEqual(self.dup_ids, [])

    def test_internal_links_resolve(self):
        missing = [a.attrs["href"] for a in self.nodes
                   if a.tag == "a" and a.attrs.get("href", "").startswith("#") and a.attrs["href"][1:] not in self.by_id]
        self.assertEqual(missing, [])

    def test_labels_point_to_inputs(self):
        bad = [lab.attrs["for"] for lab in self.nodes if lab.tag == "label" and "for" in lab.attrs
               and (lab.attrs["for"] not in self.by_id or self.by_id[lab.attrs["for"]].tag not in ("input", "select"))]
        self.assertEqual(bad, [])

    def test_storage_keys_are_unique_and_match_ids(self):
        keys = [n.attrs["data-k"] for n in self.nodes if n.tag == "input" and "data-k" in n.attrs]
        self.assertEqual(len(keys), len(set(keys)), "data-k 중복")
        mismatch = [n.attrs["data-k"] for n in self.nodes
                    if n.tag == "input" and "data-k" in n.attrs and n.attrs.get("id") != n.attrs["data-k"]]
        self.assertEqual(mismatch, [])

    def test_heading_levels_do_not_skip(self):
        levels = [int(n.tag[1]) for n in self.nodes if re.fullmatch(r"h[1-6]", n.tag)]
        self.assertEqual(levels[0], 1, "첫 제목은 h1")
        jumps = [(a, b) for a, b in zip(levels, levels[1:]) if b > a + 1]
        self.assertEqual(jumps, [], "제목 단계를 건너뛰면 화면 낭독기 탐색이 어려워집니다")

    # 진도와 차례 ----------------------------------------------------------
    def test_done_boxes_belong_to_their_section(self):
        for i in (n for n in self.nodes if n.tag == "input" and "data-ch" in n.attrs):
            sec = i.closest(is_section_ch)
            self.assertIsNotNone(sec, i.attrs["data-ch"])
            self.assertEqual(sec.attrs["id"], i.attrs["data-ch"])

    def test_progress_counters_match_done_boxes(self):
        done = [n.attrs["data-ch"] for n in self.nodes if n.tag == "input" and "data-ch" in n.attrs]
        for part in ("p1", "p2", "p3"):
            n = sum(1 for d in done if d.startswith(part + "-"))
            self.assertGreater(n, 0, part)
            self.assertEqual(self.by_id["c-" + part].text().strip(), f"0/{n}")
        self.assertEqual(self.by_id["progTxt"].text().strip(), f"끝낸 장 0 / {len(done)}")

    def test_toc_matches_sections(self):
        toc = [a.attrs["data-toc"] for a in self.nodes if a.tag == "a" and "data-toc" in a.attrs]
        self.assertEqual(sorted(toc), sorted(s.attrs["id"] for s in self.sections))
        for a in (n for n in self.nodes if n.tag == "a" and "data-toc" in n.attrs):
            self.assertEqual(a.attrs["href"], "#" + a.attrs["data-toc"])

    # 학습 카드 ------------------------------------------------------------
    def test_flashcards_are_well_formed(self):
        ids = [c.attrs.get("data-fc") for c in self.cards]
        self.assertEqual(len(ids), len(set(ids)))
        for c in self.cards:
            sec = c.closest(is_section_ch)
            self.assertTrue(c.attrs["data-fc"].startswith(sec.attrs["id"] + "-f"), c.attrs["data-fc"])
            q = [n for n in c.iter() if "fc-q" in n.classes]
            a = [n for n in c.iter() if "fc-a" in n.classes]
            self.assertEqual(len(q), 1, c.attrs["data-fc"])
            self.assertEqual(len(a), 1, c.attrs["data-fc"])
            self.assertTrue(q[0].text().strip() and a[0].text().strip(), c.attrs["data-fc"])
            self.assertEqual(c.children[0].tag if isinstance(c.children[0], Node) else None, "summary")

    def test_flashcard_counts_are_consistent(self):
        total = len(self.cards)
        self.assertEqual(self.by_id["fcTotalCover"].text().strip(), str(total))
        self.assertEqual(self.by_id["dkPos"].text().strip(), f"1 / {total}")
        self.assertIn(f"표시 안 한 카드 {total}", self.by_id["dkStats"].text())
        per = {}
        for c in self.cards:
            sid = c.closest(is_section_ch).attrs["id"]
            per[sid] = per.get(sid, 0) + 1
        for a in (n for n in self.nodes if n.tag == "a" and "data-deck" in n.attrs):
            target = a.attrs["data-deck"]
            if target == "all":
                continue
            self.assertIn(target, per, f"카드가 없는 장을 가리키는 덱 링크: {target}")
            small = [n for n in a.iter() if n.tag == "small"][0].text()
            m = re.search(r"학습 카드 (\d+)장", small)
            self.assertIsNotNone(m, small)
            self.assertEqual(int(m.group(1)), per[target], target)

    # 과제·프롬프트 카드 ------------------------------------------------------
    def test_task_cards_show_correct_criteria_count(self):
        tcards = [n for n in self.nodes if n.tag == "div" and "tcard" in n.classes]
        self.assertGreater(len(tcards), 0)
        for t in tcards:
            self.assertIn("id", t.attrs)
            boxes = [n for n in t.iter() if n.tag == "input" and "data-k" in n.attrs]
            count = [n for n in t.iter() if "tc-count" in n.classes][0].text().strip()
            self.assertEqual(count, f"기준 0/{len(boxes)}", t.attrs["id"])
            self.assertGreater(len(boxes), 0, t.attrs["id"])

    def test_prompt_cards_have_copy_button_and_code(self):
        figs = [n for n in self.nodes if n.tag == "figure" and "prompt" in n.classes]
        self.assertGreater(len(figs), 0)
        for f in figs:
            self.assertTrue(any(n.tag == "button" and "copy" in n.classes for n in f.iter()))
            code = [n for n in f.iter() if n.tag == "code" and n.parent.tag == "pre"]
            self.assertEqual(len(code), 1)
            self.assertGreater(len(code[0].text().strip()), 40)

    # 용어와 내용 -----------------------------------------------------------
    def test_banned_terms_are_absent(self):
        for path in (HTML_PATH, README_PATH):
            text = path.read_text(encoding="utf-8")
            self.assertIsNone(BANNED_KO.search(text), f"{path.name}: 「특수체육」으로 통일합니다")
            self.assertIsNone(re.search(r"adapted\s+physical", text, re.I), path.name)

    def test_heart_rate_example_matches_formula(self):
        age = 54
        hrmax = 208 - 0.7 * age
        lo, hi = round(hrmax * 0.64), round(hrmax * 0.76)
        self.assertEqual(round(hrmax), 170)
        self.assertIn(f"{lo}–{hi}회", self.src)
        self.assertIn("약 170회", self.src)

    def test_logmar_examples_match_formula(self):
        self.assertAlmostEqual(10 ** -1.0, 0.1)
        self.assertEqual(round(10 ** -1.4, 2), 0.04)
        self.assertEqual(round(10 ** -1.5, 2), 0.03)
        self.assertEqual(round(10 ** -2.6, 4), 0.0025)
        self.assertIn("LogMAR 1.0은 소수 시력 0.1, 1.4는 약 0.04, 1.5는 약 0.03, 2.6은 약 0.0025", self.src)

    def test_unverified_values_are_flagged(self):
        text = re.sub(r"<[^>]+>", "", self.src)
        for phrase in ("교정시력 0.06 이하", "세부 규격은 개정이 잦으므로", "반칙의 세부 처리는"):
            i = text.find(phrase)
            self.assertNotEqual(i, -1, phrase)
            self.assertIn("확인 필요", text[i:i + 120], phrase)

    def test_lesson_plans_follow_six_steps_and_last_50_minutes(self):
        for sid in ("p3-a", "p3-b", "p3-c"):
            sec = self.by_id[sid]
            rows = [r for r in sec.iter() if r.tag == "tr" and r.parent.tag == "tbody"]
            cells = [[c.text().strip() for c in r.iter() if c.tag == "td"] for r in rows]
            self.assertEqual(len(cells), 6, sid)
            for step, row in zip(SIX_STEPS, cells):
                self.assertIn(step, row[0], sid)
            minutes = sum(int(re.match(r"(\d+)분", row[1]).group(1)) for row in cells)
            self.assertEqual(minutes, 50, sid)
            self.assertIn("80%", cells[2][4], sid)
            self.assertIn("95%", cells[4][4], sid)

    # 아티팩트 계약 ----------------------------------------------------------
    def test_external_resources_are_allowed_hosts_only(self):
        for n in self.nodes:
            if n.tag == "script":
                self.assertNotIn("src", n.attrs, "외부 스크립트를 쓰지 않습니다")
            if n.tag == "link" and n.attrs.get("href", "").startswith("http"):
                self.assertRegex(n.attrs["href"], r"^https://fonts\.(googleapis|gstatic)\.com")
            if n.tag == "img":
                self.assertFalse(n.attrs.get("src", "").startswith("http"))

    def test_artifact_fragment_contract(self):
        start = self.src.index(FRAG_START)
        end = self.src.index(FRAG_END)
        frag = self.src[self.src.index("\n", start) + 1:end]
        self.assertIsNone(re.search(r"<!doctype|<(html|head|body)[\s>]", frag, re.I))
        head = frag.encode("utf-8")[:8192].decode("utf-8", "ignore")
        self.assertIn("<title>특수체육 시각장애 교재</title>", head)
        self.assertIn('<meta name="claude:viewport-fit-sides" content="cover">', head)

    def test_theme_tokens_defined_for_both_themes(self):
        style = re.search(r"<style>\s*/\* Layout:(.*?)</style>", self.src, re.S).group(1)
        light = css_tokens(re.search(r"\n:root\{(.*?)\}", style, re.S).group(1))
        dark_media = css_tokens(re.search(r'@media \(prefers-color-scheme:dark\)\{:root:not\(\[data-theme="light"\]\)\{(.*?)\}\}', style, re.S).group(1))
        dark_attr = css_tokens(re.search(r':root\[data-theme="dark"\]\{(.*?)\}', style, re.S).group(1))
        self.assertEqual(dark_media, dark_attr, "두 다크 블록은 같은 값이어야 합니다")
        self.assertLessEqual(set(dark_media), set(light), "다크 블록에만 있는 토큰이 있으면 밝은 테마에서 색이 빠집니다")
        for block in re.findall(r'\[data-contrast="high"\]\{(.*?)\}', style, re.S):
            self.assertLessEqual(set(css_tokens(block)), set(light))


if __name__ == "__main__":
    unittest.main()
