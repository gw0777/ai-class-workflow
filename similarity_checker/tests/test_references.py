from similarity_checker import references as R

DOC = """본문입니다. 협동학습은 효과적이다.
본문 둘째 문장입니다.
본문 셋째 문장입니다.
본문 넷째 문장입니다.

참고문헌
김철수(2020). 특수체육에서 협동학습의 효과. 한국특수체육학회지, 28(1), 1-20.
Johnson, D. W., & Johnson, R. T. (2009). An educational psychology success story: Social interdependence
    theory and cooperative learning. Educational Researcher, 38(5), 365-379. https://doi.org/10.3102/0013189X09339057
[3] Siedentop, D. (1994). Sport education: Quality PE through positive sport experiences. Human Kinetics.
"""


def test_extract_and_parse_references():
    refs = R.extract_references(DOC)
    assert len(refs) == 3
    assert refs[0].authors == "김철수" and refs[0].year == "2020"
    assert refs[0].title == "특수체육에서 협동학습의 효과"
    assert refs[1].doi == "10.3102/0013189X09339057" and refs[1].year == "2009"
    assert refs[1].title.startswith("An educational psychology success story")
    assert refs[2].title.startswith("Sport education") and refs[2].year == "1994"


def test_no_reference_section():
    assert R.extract_references("본문만 있는 문서입니다.") == []


class FakeClient:
    """Crossref/OpenAlex 응답을 흉내 내는 클라이언트."""

    def __init__(self, crossref_items=None, doi_ok=True, openalex_items=None, fail=False):
        self.crossref_items = crossref_items or []
        self.openalex_items = openalex_items or []
        self.doi_ok = doi_ok
        self.fail = fail
        self.calls = []

    def get_json(self, url, params=None, headers=None):
        self.calls.append(url)
        if self.fail:
            raise ConnectionError("network down")
        if "crossref" in url and "/works/" in url:
            if not self.doi_ok:
                raise ValueError("404")
            return {"message": {"title": ["An educational psychology success story: Social interdependence theory and cooperative learning"],
                                "DOI": "10.3102/0013189x09339057", "URL": "https://doi.org/10.3102/0013189x09339057"}}
        if "crossref" in url:
            return {"message": {"items": self.crossref_items}}
        if "openalex" in url:
            return {"results": self.openalex_items}
        raise AssertionError(url)


def test_verify_by_doi():
    refs = R.extract_references(DOC)
    r = R.verify_reference(refs[1], FakeClient())
    assert r.status == "확인" and r.score >= 0.85


def test_verify_by_bibliographic_search_confirmed():
    ref = R.parse_reference("Siedentop, D. (1994). Sport education: Quality PE through positive sport experiences. Human Kinetics.")
    client = FakeClient(crossref_items=[{"title": ["Sport Education: Quality PE Through Positive Sport Experiences"],
                                         "DOI": "10.1/abc", "URL": "https://doi.org/10.1/abc",
                                         "issued": {"date-parts": [[1994]]}, "author": []}])
    r = R.verify_reference(ref, client)
    assert r.status == "확인" and r.doi == "10.1/abc"


def test_verify_falls_back_to_openalex_and_flags_unconfirmed():
    ref = R.parse_reference("김철수(2020). 존재하지 않는 가짜 논문 제목입니다. 가상학회지, 1(1), 1-2.")
    client = FakeClient(crossref_items=[{"title": ["Totally unrelated work"], "DOI": "10.9/zzz", "issued": {"date-parts": [[2001]]}}],
                        openalex_items=[{"title": "Another unrelated thing", "publication_year": 2020, "id": "W1"}])
    r = R.verify_reference(ref, client)
    assert r.status == "미확인"
    assert any("openalex" in c for c in client.calls)


def test_verify_all_offline_and_network_failure():
    refs = R.extract_references(DOC)
    offline = R.verify_all(refs, online=False)
    assert all(x["status"] == "오프라인" for x in offline)
    failed = R.verify_all(R.extract_references(DOC), client=FakeClient(fail=True))
    assert all(x["status"] == "오프라인" for x in failed)
    assert R.summarize(failed)["오프라인"] == 3
