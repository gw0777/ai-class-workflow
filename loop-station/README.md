# 루프 스테이션 (Loop Station)

**98/100점 이상만 통과**하는 품질 게이트 루프와, 그 검수·기록을 HTML로 남기는 시스템.
에이전트 운영 규약은 저장소 루트의 [`agent.md`](../agent.md) 참조.

## 디렉터리 구조

```
loop-station/
├── rubrics/            # 유형별 100점 루브릭 + 공통 감점표(_common.md)
├── deliverables/       # 실행별 산출물 (<run_id>/ 아래)
├── records/            # 실행별 검수 기록 JSON (<run_id>.json)
├── site/               # 생성된 검수 보고서·대시보드 HTML (커밋됨, build로 재생성)
├── tools/loopstation.py# 검증(validate) + HTML 생성(build) 도구 (표준 라이브러리만 사용)
└── tests/              # 단위 테스트
```

## 사용법

```bash
# 기록 검증 (인자 생략 시 records/ 전체)
python3 loop-station/tools/loopstation.py validate

# 검수 보고서 + 대시보드 생성 → 브라우저로 loop-station/site/index.html 열기
python3 loop-station/tools/loopstation.py build

# 새 기록 스켈레톤 출력
python3 loop-station/tools/loopstation.py new --type education --title "제목"

# 테스트
python3 -m unittest discover -s loop-station/tests
```

## 기록 JSON 스키마 (schema_version 1)

| 키 | 타입 | 설명 |
|---|---|---|
| `schema_version` | int | 항상 `1` |
| `run_id` | str | `YYYYMMDD-HHMMSS-slug` (영소문자/숫자/하이픈). 파일명은 `<run_id>.json` |
| `created_at` | str | ISO 8601 시각 |
| `type` | str | `education` \| `html_report` \| `document` \| `general` |
| `title` | str | 산출물 제목 |
| `rubric` | str | 사용한 루브릭 경로 |
| `gate_threshold` | num | 게이트 점수 (기본 98) |
| `requirements_summary` | str | 사용자 요구 요약 |
| `deliverables` | list | `{path, format, description}` — 1개 이상 |
| `iterations` | list | 회전별 채점 기록 — 1~5개 (아래 참조) |
| `final_total` | num | 마지막 회전의 `total`과 동일해야 함 |
| `passed` | bool | `final_total >= gate_threshold`와 일치해야 함 |
| `notes` | str | 비고 (선택) |

### `iterations[]` 항목

| 키 | 타입 | 설명 |
|---|---|---|
| `round` | int | 1부터 1씩 증가 |
| `total` | num | **`criteria` 점수 합과 일치해야 함** (정본) |
| `criteria` | list | `{category, item, score(0~5), max(=5), comment}` — 코멘트 필수 |
| `deductions` | list | `{severity(critical\|major\|minor), points(음수), where, reason, fix_directive}` |
| `verdict` | str | `pass` \| `revise` — 마지막 회전은 `passed`와 일치해야 함 |

### 검증기가 강제하는 무결성 규칙

- 회전 1: **총점 95점 상한 + 감점(개선점) 3건 이상** (자체 채점 인플레이션 방지)
- 통과 시 앵커 규칙: 마지막 회전이 **치명 0건 + 중대 0건 + 경미 최대 2건**
- 최대 5회전, `final_total`/`passed`/마지막 `verdict` 상호 일관성

## 새 유형 루브릭 추가 방법

1. `rubrics/<새유형>.md` 작성 — `_common.md`의 5카테고리 × 4항목 × 5점 구조를 따른다.
2. `tools/loopstation.py`의 `TYPES`, `TYPE_LABELS`에 유형을 추가한다.
3. `agent.md` ①단계의 유형 목록에 추가한다.
