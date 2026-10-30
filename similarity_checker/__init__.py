"""similarity_checker — 카피킬러 대체용 개인 논문 유사도·표절 검사 도구.

구성
----
- extract.py       : PDF/DOCX/PPTX/HWPX/TXT/MD/HTML → 본문 텍스트 추출
- textproc.py      : 문장 분리(한국어), 어절 토큰화, 조사 제거(loose), n-gram 지문, 제외 규칙
- index.py         : SQLite 로컬 문헌 코퍼스(역색인) 관리
- compare.py       : 1:N(코퍼스) / 1:1 유사도 비교 엔진 (6어절 연속 일치 + 유사 문장)
- references.py    : 참고문헌 파싱 + 실존 여부 검증(Crossref/OpenAlex)
- online.py        : 기존 문헌 유무(제목/문장) 온라인 검사
- github_source.py : GitHub 저장소에서 문서를 수집해 코퍼스에 추가
- report.py        : HTML / Markdown / JSON 리포트
- cli.py           : 명령행 인터페이스 (python -m similarity_checker ...)
"""
__version__ = "0.1.0"
