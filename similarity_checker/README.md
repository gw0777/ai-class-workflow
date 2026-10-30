# similarity_checker — 개인용 논문 유사도·표절 검사 도구 (카피킬러 대체)

KCI 논문 유사도 검사 서비스 중단(2026-10-23~)과 카피킬러 유료 상세보기(건당 9,900원)를 대신해,
**내 PC와 GitHub 저장소에 있는 문헌을 코퍼스로 삼아** 논문·보고서·수업자료의 유사도를 검사하는 도구입니다.
외부 서비스에 문서를 올리지 않으며, 핵심 기능은 표준 라이브러리만으로 동작합니다.

## 무엇을 하나

| 기능 | 카피킬러 대응 기능 | 명령 |
|------|------------------|------|
| 로컬 문헌 코퍼스 구축(PDF/DOCX/PPTX/HWPX/TXT/MD/HTML) | 비교 문헌 DB | `index add` |
| GitHub 저장소의 문서를 수집해 코퍼스에 추가 | — | `index add-github` |
| 코퍼스 대비 유사도 검사(1:N) + 표절률·출처별 일치율·문장 하이라이트 | 표절검사 + 상세보기 | `check` |
| 두 문서 1:1 비교 | 1:1 비교 | `compare` |
| 참고문헌 파싱 + Crossref/OpenAlex 실존 검증(가짜 인용 탐지) | — | `refs --online` |
| 기존 문헌 유무(제목 기반 로컬+온라인, GitHub 코드검색 선택) | — | `exists` |
| 인용문·출처표시·참고문헌·목차 제외, 6어절 연속 일치 기준 | 검사 설정 | `--min-run`, `--no-exclude-*` |
| HTML / Markdown / JSON 리포트, CI용 종료코드 | 결과 보고서 | `--out-dir`, `--fail-above` |

## 설치

```bash
pip install -r similarity_checker/requirements.txt   # pdfplumber, pypdf, python-docx, python-pptx, requests, pytest
```
`pdftotext`(poppler)가 있으면 PDF 추출이 가장 빠릅니다(없어도 동작). HWP(구형)는 미지원 → HWPX/DOCX/PDF로 저장 후 사용.
스캔본 PDF는 텍스트가 없어 건너뜁니다(OCR 후 TXT로 넣으세요).

## 빠른 시작

```bash
# 1) 비교 문헌 코퍼스 만들기 (폴더째 가능; 기본 DB는 ./.simcheck/corpus.db, 환경변수 SIMCHECK_DB)
python -m similarity_checker index add ./papers ./lectures *.pdf

# 2) GitHub 저장소의 문서도 코퍼스에 (owner/repo[@branch][:하위경로]; 비공개면 GITHUB_TOKEN)
python -m similarity_checker index add-github gw0777/ai-class-workflow
python -m similarity_checker index add-github gw0777/papers@main:published/

# 3) 검사 — 표절률·출처·하이라이트 리포트 생성
python -m similarity_checker check 내논문.docx --out-dir reports
python -m similarity_checker check 내논문.docx --refs --online --exists --html r.html   # 참고문헌 검증 + 기존문헌 유무 포함

# 4) 1:1 비교, 참고문헌만 검증, 기존 문헌 유무만 조회
python -m similarity_checker compare 초안_v1.docx 초안_v2.docx --html diff.html
python -m similarity_checker refs 내논문.pdf --online
python -m similarity_checker exists --title "특수체육에서 협동학습이 사회성에 미치는 영향"

# 코퍼스 관리
python -m similarity_checker index list | stats | remove 3
```

### 결과 읽는 법
- **표절률**: 의심 문장(일치 또는 유사)의 어절 수 ÷ 검사 어절 수. 등급: 5% 미만 안전 / 15% 주의 / 30% 경고 / 그 이상 위험(참고용).
- **정확일치율**: `--min-run`(기본 6) 어절 이상 연속 일치한 어절만 센 비율(엄격).
- **일치(빨강)**: 6어절 이상 연속 일치. **유사(주황)**: 연속 일치는 없지만 어절/글자 시퀀스 유사도가 `--sim-threshold`(기본 0.7) 이상 — 조사만 바꾼 바꿔쓰기 의심.
- **제외(회색)**: 인용문·출처표시·목차·짧은 문장·숫자표. 카피킬러처럼 `--no-exclude-quotes` 등으로 끌 수 있음.
- **코퍼스 중복도**: 이 문서의 지문이 코퍼스에 이미 존재하는 비율. 60% 이상이면 이미 색인된(=이미 제출/게재된) 문서일 가능성.
- 같은 파일이 코퍼스에 들어 있으면 자동으로 비교에서 제외합니다(`--exclude-source 문자열`로 추가 제외).

## 검사 알고리즘(요약)
1. 추출 → 정규화(글자마다 띄어진 PDF 복원, 줄바꿈 병합) → 한국어 문장 분리(마침표 없는 슬라이드형 텍스트는 40어절 단위 분할).
2. 어절 토큰화 + 흔한 조사/어미 제거(`--strict`로 끔) → 어절 3-gram 해시 역색인(SQLite).
3. 문장마다 역색인 후보 상위 N개를 `difflib` 시퀀스 정렬로 정밀 비교 → 연속 일치 어절 / 유사도 산출.
4. 출처별 집계, 하이라이트 리포트. 형태소 분석기 없이 동작하므로 설치가 가볍고, 필요 시 `textproc.py`의 조사 목록만 조정하면 됩니다.

## 참고문헌 실존 검증
`참고문헌`/`References` 표제 아래 항목을 파싱(저자·연도·제목·DOI)하고 Crossref(DOI 직접 조회 → 서지 검색) → OpenAlex 순으로 제목 유사도를 비교합니다.
- 확인(≥0.85) / 의심(0.6~0.85, 서지사항 확인 필요) / 미확인 / 오프라인.
- 국내 학술지·학위논문은 Crossref 미등재가 많아 **미확인이 곧 가짜는 아닙니다** → RISS/KCI에서 수동 확인. 반대로 LLM이 만든 논문 초안(`paper_pipeline_v2`)의 영문 참고문헌은 이 검증으로 환각 인용을 걸러낼 수 있습니다.
- `CROSSREF_MAILTO=you@example.com` 을 설정하면 Crossref polite pool을 사용합니다.

## GitHub 활용
- **코퍼스 저장소**: 과거 논문·발표자료를 `papers/` 같은 저장소에 모아두고 `index add-github` 로 어디서든 같은 코퍼스를 재구성.
- **Actions 워크플로**(`.github/workflows/similarity-check.yml`): Actions 탭 → *Similarity check* → *Run workflow* 에서 파일 경로를 입력하면 저장소 문서(및 지정 코퍼스 저장소)를 색인해 검사하고 HTML/MD/JSON 리포트를 아티팩트로 올립니다. `fail_above` 를 주면 기준 초과 시 실패 처리.
- **기존 문헌 유무**: `exists --github-phrases 3` 은 대표 문장 3개를 GitHub 코드검색으로 찾습니다(`GITHUB_TOKEN` 필요).

## 테스트
```bash
python -m pytest -q similarity_checker/tests     # 네트워크 불필요(온라인 API는 가짜 클라이언트로 검증)
```

## 한계와 주의
- 코퍼스에 없는 문헌과의 유사성은 찾을 수 없습니다(카피킬러처럼 수십억 건 웹·학술 DB를 갖고 있지 않음). 비교 대상을 꾸준히 쌓는 것이 핵심입니다.
- 의미 수준 바꿔쓰기(동의어 치환, 문장 구조 변경)는 어절 기반으로는 잡기 어렵습니다. 필요하면 `compare.py`에 임베딩 기반 비교를 추가할 수 있도록 문장 단위로 설계되어 있습니다.
- 결과는 자체 점검용입니다. 학회 투고 시 공식 검사 서비스 요구사항은 별도로 확인하세요.
