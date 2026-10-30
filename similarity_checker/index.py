"""로컬 문헌 코퍼스(SQLite): 문서·문장·어절 n-gram 역색인."""
from __future__ import annotations

import datetime
import json
import os
import sqlite3
from dataclasses import dataclass
from typing import Iterable

from .config import CheckConfig
from .textproc import TOKENIZER_VERSION, Sentence, prepare_sentences, shingles, text_sha256

_SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY,
    source TEXT UNIQUE NOT NULL,
    title TEXT,
    kind TEXT,
    sha256 TEXT,
    n_sentences INTEGER,
    n_tokens INTEGER,
    added_at TEXT,
    meta TEXT
);
CREATE TABLE IF NOT EXISTS sentences (
    id INTEGER PRIMARY KEY,
    doc_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    idx INTEGER NOT NULL,
    text TEXT NOT NULL,
    ltokens TEXT NOT NULL,
    n_tokens INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sent_doc ON sentences(doc_id);
CREATE TABLE IF NOT EXISTS shingles (
    hash INTEGER NOT NULL,
    sent_id INTEGER NOT NULL REFERENCES sentences(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_shingle_hash ON shingles(hash);
CREATE INDEX IF NOT EXISTS idx_shingle_sent ON shingles(sent_id);
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT);
"""


@dataclass
class DocRecord:
    id: int
    source: str
    title: str
    kind: str
    sha256: str
    n_sentences: int
    n_tokens: int
    added_at: str


class CorpusIndex:
    def __init__(self, path: str = ":memory:", ngram: int = 3):
        if path != ":memory:":
            os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
        self.path = path
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys=ON")
        if path != ":memory:":
            self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.executescript(_SCHEMA)
        self.warnings: list[str] = []
        stored = self.conn.execute("SELECT value FROM settings WHERE key='ngram'").fetchone()
        if stored is None:
            self.conn.execute("INSERT INTO settings(key, value) VALUES('ngram', ?)", (str(ngram),))
            self.conn.execute("INSERT INTO settings(key, value) VALUES('tokenizer', ?)", (str(TOKENIZER_VERSION),))
            self.conn.commit()
            self.ngram = ngram
        else:
            self.ngram = int(stored["value"])
            tv = self.conn.execute("SELECT value FROM settings WHERE key='tokenizer'").fetchone()
            if tv is None or int(tv["value"]) != TOKENIZER_VERSION:
                self.warnings.append(
                    f"코퍼스가 이전 토큰화 규칙(v{tv['value'] if tv else '?'})으로 만들어졌습니다(현재 v{TOKENIZER_VERSION}). "
                    "정확도를 위해 `index add` 로 다시 색인하세요(기존 DB 삭제 후)."
                )

    def close(self) -> None:
        self.conn.close()

    # ----------------------------------------------------------------- 문서 추가
    def find_by_sha(self, sha: str) -> DocRecord | None:
        row = self.conn.execute("SELECT * FROM documents WHERE sha256=?", (sha,)).fetchone()
        return self._rec(row) if row else None

    def find_by_source(self, source: str) -> DocRecord | None:
        row = self.conn.execute("SELECT * FROM documents WHERE source=?", (source,)).fetchone()
        return self._rec(row) if row else None

    def add_text(
        self,
        text: str,
        source: str,
        title: str = "",
        kind: str = "txt",
        meta: dict | None = None,
        replace: bool = True,
        cfg: CheckConfig | None = None,
    ) -> tuple[DocRecord, str]:
        """텍스트를 코퍼스에 색인. (레코드, 상태) 상태: added | replaced | skipped-duplicate"""
        cfg = cfg or CheckConfig()
        sha = text_sha256(text)
        existing = self.find_by_source(source)
        if existing:
            if existing.sha256 == sha:
                return existing, "skipped-duplicate"
            if not replace:
                return existing, "skipped-exists"
            self.remove(existing.id)
        same = self.find_by_sha(sha)
        if same:
            return same, "skipped-duplicate"

        # 코퍼스 문장은 제외 규칙을 적용하지 않는다(참고문헌·인용도 비교 대상이 될 수 있도록).
        idx_cfg = CheckConfig(loose=cfg.loose, exclude_quotes=False, exclude_citations=False,
                              exclude_references=False, exclude_toc=False, min_tokens=1)
        sents, _ = prepare_sentences(text, idx_cfg)
        n_tokens = sum(s.n_tokens for s in sents)
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur = self.conn.execute(
            "INSERT INTO documents(source,title,kind,sha256,n_sentences,n_tokens,added_at,meta) VALUES(?,?,?,?,?,?,?,?)",
            (source, title, kind, sha, len(sents), n_tokens, now, json.dumps(meta or {}, ensure_ascii=False)),
        )
        doc_id = cur.lastrowid
        self._insert_sentences(doc_id, sents)
        self.conn.commit()
        return self.get(doc_id), "added"

    def _insert_sentences(self, doc_id: int, sents: Iterable[Sentence]) -> None:
        rows = []
        for s in sents:
            if s.n_tokens == 0:
                continue
            cur = self.conn.execute(
                "INSERT INTO sentences(doc_id, idx, text, ltokens, n_tokens) VALUES(?,?,?,?,?)",
                (doc_id, s.idx, s.text, " ".join(s.ltokens), s.n_tokens),
            )
            sid = cur.lastrowid
            rows.extend((h, sid) for h in shingles(s.ltokens, self.ngram))
        self.conn.executemany("INSERT INTO shingles(hash, sent_id) VALUES(?,?)", rows)

    # ----------------------------------------------------------------- 조회/삭제
    def _rec(self, row) -> DocRecord:
        return DocRecord(row["id"], row["source"], row["title"] or "", row["kind"] or "", row["sha256"] or "",
                         row["n_sentences"] or 0, row["n_tokens"] or 0, row["added_at"] or "")

    def get(self, doc_id: int) -> DocRecord:
        row = self.conn.execute("SELECT * FROM documents WHERE id=?", (doc_id,)).fetchone()
        if not row:
            raise KeyError(doc_id)
        return self._rec(row)

    def list(self) -> list[DocRecord]:
        return [self._rec(r) for r in self.conn.execute("SELECT * FROM documents ORDER BY id")]

    def remove(self, doc_id: int) -> bool:
        cur = self.conn.execute("DELETE FROM documents WHERE id=?", (doc_id,))
        self.conn.commit()
        return cur.rowcount > 0

    def stats(self) -> dict:
        q = self.conn.execute
        return {
            "path": self.path,
            "ngram": self.ngram,
            "tokenizer": TOKENIZER_VERSION,
            "documents": q("SELECT COUNT(*) FROM documents").fetchone()[0],
            "sentences": q("SELECT COUNT(*) FROM sentences").fetchone()[0],
            "shingles": q("SELECT COUNT(*) FROM shingles").fetchone()[0],
        }

    # ----------------------------------------------------------------- 검색
    def candidates(self, hashes: set[int], limit: int, exclude_doc_ids: set[int] | None = None) -> list[tuple[int, int]]:
        """지문 해시 집합과 겹치는 문장 id를 겹침 수 내림차순으로 돌려준다 [(sent_id, hits)]."""
        if not hashes:
            return []
        exclude_doc_ids = exclude_doc_ids or set()
        counts: dict[int, int] = {}
        hs = list(hashes)
        for i in range(0, len(hs), 400):  # SQLite 변수 한도 회피
            chunk = hs[i : i + 400]
            qmarks = ",".join("?" * len(chunk))
            for row in self.conn.execute(f"SELECT sent_id FROM shingles WHERE hash IN ({qmarks})", chunk):
                counts[row[0]] = counts.get(row[0], 0) + 1
        ranked = sorted(counts.items(), key=lambda kv: -kv[1])
        out = []
        for sid, hits in ranked:
            if exclude_doc_ids:
                d = self.conn.execute("SELECT doc_id FROM sentences WHERE id=?", (sid,)).fetchone()
                if d and d[0] in exclude_doc_ids:
                    continue
            out.append((sid, hits))
            if len(out) >= limit:
                break
        return out

    def sentence(self, sent_id: int) -> dict:
        r = self.conn.execute(
            "SELECT s.id, s.doc_id, s.idx, s.text, s.ltokens, s.n_tokens, d.source, d.title "
            "FROM sentences s JOIN documents d ON d.id=s.doc_id WHERE s.id=?",
            (sent_id,),
        ).fetchone()
        return dict(r) if r else {}

    def overlap_ratio(self, hashes: set[int]) -> float:
        """문서 지문 중 코퍼스에 이미 존재하는 비율(중복 문서 감지용)."""
        if not hashes:
            return 0.0
        hs = list(hashes)
        found = 0
        for i in range(0, len(hs), 400):
            chunk = hs[i : i + 400]
            qmarks = ",".join("?" * len(chunk))
            found += self.conn.execute(f"SELECT COUNT(DISTINCT hash) FROM shingles WHERE hash IN ({qmarks})", chunk).fetchone()[0]
        return found / len(hashes)

    def search_title(self, title: str) -> list[tuple[DocRecord, float]]:
        """코퍼스 문서 제목과의 유사도(0~1) 상위 목록."""
        import difflib

        key = "".join(title.lower().split())
        res = []
        for d in self.list():
            r = difflib.SequenceMatcher(None, key, "".join(d.title.lower().split()), autojunk=False).ratio()
            if r >= 0.5:
                res.append((d, r))
        return sorted(res, key=lambda x: -x[1])
