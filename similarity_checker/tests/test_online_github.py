from similarity_checker import online as O
from similarity_checker.github_source import RepoSpec, fetch_repo_documents, list_repo_files


class FakeClient:
    def __init__(self, routes):
        self.routes = routes

    def get_json(self, url, params=None, headers=None):
        for key, val in self.routes.items():
            if key in url:
                if isinstance(val, Exception):
                    raise val
                return val
        raise AssertionError(url)


def test_title_similarity():
    assert O.title_similarity("협동학습의 효과", "협동 학습의 효과!") == 1.0
    assert O.title_similarity("abc", "") == 0.0


def test_check_existence_merges_providers_and_errors():
    client = FakeClient({
        "crossref": {"message": {"items": [{"title": ["Cooperative learning in physical education"], "DOI": "10.1/x",
                                             "URL": "https://doi.org/10.1/x", "issued": {"date-parts": [[2010]]}, "author": []}]}},
        "openalex": ConnectionError("blocked"),
    })
    res = O.check_existence("Cooperative Learning in Physical Education", client=client)
    assert res["hits"][0]["provider"] == "crossref" and res["hits"][0]["score"] >= 0.9
    assert res["verdict"].startswith("기존 문헌")
    assert res["errors"] and "openalex" in res["errors"][0]


def test_github_code_search_requires_token(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    try:
        O.github_code_search("some phrase", FakeClient({}))
        assert False
    except RuntimeError as e:
        assert "GITHUB_TOKEN" in str(e)


def test_pick_sample_sentences():
    sents = ["짧은 문장", "숫자 1 2 3 4 5 가 많은 문장이라서 제외되어야 하는 문장입니다 정말로", "이 문장은 길이가 충분히 길고 숫자가 없어서 대표 문장으로 선택되기에 적합한 문장입니다."]
    assert O.pick_sample_sentences(sents, k=2) == [sents[2]]


def test_repo_spec_parse():
    s = RepoSpec.parse("https://github.com/gw0777/papers@main:published/2025")
    assert (s.owner, s.repo, s.ref, s.path) == ("gw0777", "papers", "main", "published/2025")
    assert RepoSpec.parse("a/b").ref is None


def test_fetch_repo_documents_with_fake_downloader():
    client = FakeClient({
        "/repos/o/r/git/trees/main": {"tree": [
            {"type": "blob", "path": "docs/a.md", "size": 10, "sha": "1"},
            {"type": "blob", "path": "docs/b.exe", "size": 10, "sha": "2"},
            {"type": "blob", "path": "other/c.txt", "size": 10, "sha": "3"},
            {"type": "tree", "path": "docs", "size": 0, "sha": "4"},
        ]},
        "/repos/o/r": {"default_branch": "main"},
    })
    ref, files = list_repo_files(RepoSpec.parse("o/r:docs"), client)
    assert ref == "main" and [f["path"] for f in files] == ["docs/a.md"]
    docs = list(fetch_repo_documents("o/r:docs", client=client, downloader=lambda p: "# 제목\n본문 문장입니다. 둘째 문장.".encode()))
    assert len(docs) == 1
    label, title, text, kind, _ = docs[0]
    assert label == "github:o/r@main/docs/a.md" and title == "제목" and "본문 문장" in text and kind == "md"
