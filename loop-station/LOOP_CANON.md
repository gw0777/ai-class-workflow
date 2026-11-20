# 루프 정석 (Loop Canon)

기존 루프 스테이션(98점 품질 게이트)을 **'자가진단 루브릭' 단계로 품고**, 그 앞뒤에 트리거·커넥터·메모리·서브에이전트·워크트리·사람 검토를 붙여 **스스로 일하는 루프**로 확장한 것이다.

```
 ① 트리거 ──→ ② 커넥터 ──→ ③ 메모리 ──→ ④ 서브에이전트(병렬) ──→ ⑤ 워크트리 병합 ──→ ⑥ 스킬 자가진단 ──→ ⑦ 사람 검토
 시간/이벤트    읽기·쓰기    상태·이력·     같은 group = 동시 실행     각자 결과 보존 +      완료 3조건 +          승인해야 완료
 due / match   (MCP)        평가·컨텍스트   workers/<role>/            충돌 표시·실패 격리   98점 게이트 + 회전 상한  교훈 → 스킬 메모리
                            + 스킬 메모리                              merge                 check                  review
                 ▲                                                                              │ 미충족(다음 회전)
                 └──────────────────────────── 최대 max_rounds 회전 ─────────────────────────────┘ 상한 도달 → 중단(halted)
```

### 야생 학습 4모드와 겹쳐 보기 (2회차 보강)

책 『2장 에센스 체험』 69쪽의 '야생 학습의 네 가지 모드'(옵션 → 가설 → 멘탈 시뮬레이션 → 액관해 → 지도 → 멘탈 레프리젠테이션)를 루프 정석 위에 올려 보니 빈 칸 셋이 보였고, 이를 채웠다.

| 야생 학습 | 루프 정석에서 맡는 부분 | 1회차 | 2회차 보강 |
|---|---|---|---|
| 옵션 (미래 × 분산) | `report.options` — 고르기 전에 넓게 늘어놓은 길 `{name, reason}` | 약함 (병렬 수집만) | `stop_conditions.min_options`개 이상 필수 |
| 가설 (미래 × 집중) | `report.chosen` + 성공 기준·중단 조건 | 갖춤 | 고른 길이 options 안에 있어야 하고 이유 필수 |
| 멘탈 시뮬레이션 (다리) | `simulate` — start와 같은 가드를 돌리되 아무것도 만들지 않음 | 도구만 있음 | 정식 명령으로 추가 |
| 액관해 (과거·현재 × 집중) | `start → merge → check` | 갖춤 | — |
| 지도 (과거·현재 × 분산) | 메모리 4종 | 갖춤 | — |
| 멘탈 레프리젠테이션 (다리) | 스킬 메모리 → `report.lessons_applied` | 읽기만 함 | 교훈이 있으면 반영 기록 또는 미반영 이유 필수 (지어낸 교훈은 거부) |

> '액관해'는 책의 정의를 아직 확인하지 못했다. 여기서는 그림 속 자리(과거·현재 × 집중), 즉 실제로 한 일과 결과에 집중하는 단계로만 쓴다.

**역할 분담**: 판단(수집·분석·작성·채점)은 에이전트가 하고, 규칙(발동·중복 방지·상한·격리·병합·중단·검토)은 `tools/loopcanon.py`가 결정론적으로 강제한다. API 키나 외부 호출 없이 동작한다(표준 라이브러리만 사용). 커넥터 호출은 에이전트가 세션 안에서 MCP로 한다.

---

## 1. 강의 녹취와 구성요소 매핑

녹취가 음성 인식이라 일부 단어가 깨져 있다. **[확인]** 은 사용자가 해석을 확인한 것, **[추정]** 은 문맥으로 해석한 것이다.

| 녹취 구절 (원문 그대로) | 해석 | 구현 위치 |
|---|---|---|
| 오토메이션 스케 · 커넥터 메모리 서보이션 | 자동화·스케줄 · 커넥터·메모리·서브에이전트 **[추정]** | 전체 7단계 |
| 시간 기반 트리거 알람 시계 … 금요일 오전 … 키워드 뉴스 수집·요약 → 이메일 | 시간 기반 트리거 | `trigger.type: schedule` · 예시 `weekly-special-pe-digest` (뉴스 대신 특수체육 논문으로 바꿈) |
| 이벤트 기반 트리거 초인종 … 메일 도착, 고객 문의, ~~음식을~~ 제출, 슬랙 키워드 | 이벤트 기반 트리거 ('음식' → '양식(폼)' **[추정]**) | `trigger.type: event` · 예시 `practicum-inquiry-triage` |
| 경로 지시와 목적적 지시 | 정해진 단계를 주는 지시 / 목표만 주는 지시 **[추정]** | `skill.instruction_mode: path \| goal` |
| 루프가 서브 에이전트를 병렬로 실행해 분석과 비교를 동시에 | 서브에이전트 병렬 | `subagents[].group` (같은 값 = 병렬) |
| 루프 워커트기하여 중간 결과를 완전하게 저장 | 워크트리로 중간 결과 격리 저장 **[추정]** | `runs/<loop_id>/<run_id>/workers/<role>/` |
| a와 b의 수정 내용은 각각 그대로 남는다. 병합할 때 서로 다른 부분을 표시 … 실패의 범위를 제한 | 격리·충돌 표시·실패 격리 | `merge` → `merged.json`의 `conflicts`, `failed_workers` |
| 스킬: 스케줄, 목적, 조건, 금지 사항, 보고 기준, 예외 처리 | 스킬 명세 | `skill.*` |
| 목적과 결과물, 사용자 … 성공의 조건이나 구체적인 수치 | 목적·결과물·사용자·수치 기준 | `skill.purpose/deliverable/user`, `success_criteria`(숫자 없으면 검증 실패) |
| 금지 사항과 그 이유 · 예외 상황과 방법 | 금지 + 이유, 예외 + 처리 | `skill.prohibitions[{rule, reason}]`, `skill.exceptions[{situation, handling}]` |
| 자가진단 루브릭이 적용된다 | 자가진단 | `skill.self_check` → 기존 `rubrics/*.md` + 98점 게이트 기록 |
| 커뮤니케이션·프로젝트 관리·데이터·디자인·웹 검색 커넥터 … MCP … 필요할 때 읽고 쓰기 | 커넥터 5분류 + 권한 | `connectors[{category, access}]` |
| 메모리가 네 가지를 기억한다: 상태, 처리 이력, 평가 기록, 컨텍스트 | 메모리 4종 **[확인]** | `memory/<loop_id>/state.json · history.jsonl · evaluations.jsonl · context.md` |
| 스킬 메모리가 있어야 루프가 성장 | 성장 층 | `memory/<loop_id>/skill-notes.md` (검토 교훈 누적, 다음 실행이 먼저 읽음) |
| 긴급도에 따른 우선 처리 | 우선순위 | `trigger.priority_rules` + `match` 대기열 |
| 요약 200자 · 개선 제안 세 가지 이상 · 첨부 파일 1개 이상 … 무한 루프를 돌지 않도록 중단 조건 | 완료 3조건 **[확인]** | `stop_conditions.summary_max_chars / min_improvements / min_attachments` |
| 부품마다 와이드의 범위 설정 하루 AI보다 조건 | 회전 상한 + 하루 실행 상한 **[확인]** | `stop_conditions.max_rounds / daily_run_cap` |
| 최후에는 사람이 검토하고 필요한 부분만 수정 | 사람 검토 | `human_review` + `review` (승인 전에는 '완료'가 아님) |

### 해석 보류 구간 (구현하지 않음 — 확인 필요)

| 시각 | 녹취 구절 | 막힌 부분 |
|---|---|---|
| 01:21 | 이벤트 기반 정에 대한 조회 프로 적 반영이 필요한 업무의 재선 | 이벤트 기반 트리거를 쓸 업무를 고르는 기준인지 |
| 02:25 | 정해진 경로 뒤로 변경하거나 고 티모 훈련이다 | '고 티모 훈련'이 무엇인지 |
| 02:46 | 중경을 쓴다 | 워크트리 구절 안의 단어 |
| 02:46 | 스캔 타임 | 스킬 구절 안의 단어 ('스킬 템플릿'?) |
| 02:46 | 후가 세상의 인증 본보는 … 기타 고 승객 | 커넥터 예시 목록의 앞부분 |
| 04:03 | 서브 에이전트가 수명이다 | 서브에이전트 수명(생명주기) 관리 규칙이 따로 있는지 |
| 04:50 | 처리의 마음에 맞는 변명 조제가 필요하다. 직원들이 동의 필요한다 | 처리 순서·조정 규칙인지 |
| 04:50 | 종모 역할이 분리가 되어서 핫돌전 이수로 … 스타핑 리스 | 역할 분리 뒤의 단어, '스타핑 리스'(중단 규칙 목록?) |
| 04:50 | 몸맥은 표류하지 않도록 결정해야 한다 | 목표·맥락 표류 방지 규칙인지 |
| 04:50 | tot 트리오브 소트 생각에 나 와 | Tree of Thoughts를 어느 단계에 쓰는지 (후보: 옵션·가설 칸 = `options`·`chosen`, 사용자 확인 대기) |

---

## 2. 루프 명세 (`loops/<loop_id>.json`, schema_version 1)

| 키 | 필수 내용 | 검증 규칙 |
|---|---|---|
| `loop_id`, `title` | 슬러그, 제목 | 파일명 = `<loop_id>.json` |
| `trigger` | `schedule`: `weekdays`, `time`(HH:MM), `utc_offset`, `window_minutes`(기본 60) / `event`: `source`, `any_keywords`, `exclude_keywords`, `priority_rules[{level, keywords}]`, `default_priority`, `utc_offset` | 시각+창이 자정을 넘으면 안 됨 · 시간대 오프셋 필수 |
| `connectors[]` | `category`(communication·project·data·design·web_search), `name`, `access`(read·write·read_write), `purpose` | **쓰기 커넥터가 하나라도 있으면 `human_review.required: true` 필수** |
| `memory.context[]` | 컨텍스트 메모리 초기 문장 | 첫 실행 때 `context.md`로 만들어짐 |
| `subagents[]` | `role`(작업 폴더 이름), `task`, `group` | role 중복 금지 |
| `worktree.isolation` | `directory`(실행 폴더 격리) · `git_worktree`(저장소 파일을 고치는 서브에이전트는 Agent 도구 `isolation: "worktree"`로 실행) | |
| `skill` | `purpose`, `deliverable`, `user`, `instruction_mode`, `steps`, `conditions`, `success_criteria`, `prohibitions`, `reporting{to, format, when}`, `exceptions`, `self_check{rubric, gate_record}` | path 지시는 steps 필수 · 성공 기준마다 숫자 필수 · 금지마다 이유 필수 · 루브릭 파일 실재 |
| `stop_conditions` | `summary_max_chars`, `min_improvements`, `min_attachments`, `min_options`(0~10, 0이면 옵션 판정 끔), `max_rounds`(≤5), `daily_run_cap` | |
| `human_review` | `required`, `reviewer`, `checklist[]` | |

## 3. 실행 절차 (CLI)

```bash
T=loop-station/tools/loopcanon.py
python3 $T validate                                         # 명세 검증 (CI에서도 실행)
python3 $T due --at 2026-11-20T09:05:00+09:00               # ① 시간 기반: 지금 발동할 루프
python3 $T match --event loop-station/loops/samples/events.json   # ① 이벤트 기반: 긴급도 → 도착 순 대기열
python3 $T simulate weekly-special-pe-digest                # 멘탈 시뮬레이션: 시작하면 어떻게 될지 (아무것도 안 만듦)
python3 $T start weekly-special-pe-digest                   # ②③④ 가드 통과 시 실행 폴더·메모리 생성
#   → 에이전트: skill-notes.md·context.md를 읽고, group별로 서브에이전트를 병렬 실행
#     각자 workers/<role>/output.json 에 {"findings": {키: 값}} 만 쓴다
python3 $T merge <run_id>                                   # ⑤ 합의/충돌/실패 정리 → merged.json
#   → 에이전트: attachments/에 산출물, report.json 작성
#     options(고려한 길) · chosen(고른 길과 이유) · lessons_applied 또는 lessons_skip_reason
#     · summary · improvements · attachments · resolutions
#     gate_record=true 이면 records/<run_id>.json 에 98점 게이트 채점 기록 (loopstation.py validate)
python3 $T check <run_id>                                   # ⑥ 통과 → 사람 검토 대기 / 미충족 → 다음 회전 / 상한 → 중단
python3 $T review <run_id> --decision approve --reviewer "담당 교수" --note "발송 승인" --lesson "다음엔 …"
python3 $T status weekly-special-pe-digest                  # 상태 + 최근 이력
```

`check`는 통과 시 종료 코드 0, 미충족·중단 시 1을 돌려주므로 자동화 루프의 분기로 쓸 수 있다.

### report.json (에이전트가 채우는 보고서)

| 키 | 야생 학습 | 판정 |
|---|---|---|
| `options[{name, reason}]` | 옵션 | `min_options`개 이상, 이름 중복 금지, 이유 필수 |
| `chosen{name, reason}` | 가설 | name이 options 안에 있어야 함 (`min_options`가 0이면 생략 가능) |
| `lessons_applied[{lesson, how}]` / `lessons_skip_reason` | 지도 → 옵션 다리 | 스킬 메모리에 교훈이 있으면 둘 중 하나 필수. `lesson`은 교훈 문구 일부(4자 이상) 또는 그 교훈의 run_id |
| `summary` | — | 공백 포함 `summary_max_chars`자 이내 |
| `improvements[]` | — | `min_improvements`건 이상 |
| `attachments[]` | — | 실행 폴더 안의 실제 파일 `min_attachments`개 이상 |
| `resolutions{key: 근거}` | — | 병합 충돌 키마다 결정 근거 |

### 가드 (거부 사유)

| 가드 | 내용 |
|---|---|
| 동시 실행 금지 | 같은 루프에 `진행 중`·`사람 검토 대기` 실행이 있으면 새 시작 거부 |
| 중복 실행 방지 | 같은 예약 슬롯·같은 이벤트 id는 한 번만 시작 |
| 일일 상한 | 루프의 시간대 기준 하루 `daily_run_cap`회 초과 시 거부하고 이력에 `blocked` 기록 (`simulate`는 기록하지 않음) |
| 회전 상한 | `check` 미충족이나 `review` 재작업 요청이 `max_rounds`에 닿으면 `중단(halted)` |
| 메모리 손상 | 이력·평가 jsonl에 깨진 줄이 있으면 거부 (상한 계산이 틀어지지 않도록 fail-closed) |
| 첨부 경로 | 실행 폴더 밖을 가리키는 첨부는 인정하지 않음 |

### 상태 전이

```
대기(idle) ─start→ 진행 중(running) ─check 통과→ 사람 검토 대기(awaiting_review) ─approve→ 완료(done)
                     ▲   │check 미충족(회전+1)            │revise(회전+1)
                     └───┴───────────────────────────────┘
                     회전 상한 도달 → 중단(halted)        * human_review.required=false 이면 check 통과 → 완료
```

## 4. 저장 위치

| 경로 | 내용 | 커밋 |
|---|---|---|
| `loops/*.json` | 루프 명세 | ✅ |
| `loops/samples/` | 예시 이벤트 (가짜 데이터, `(예시 데이터)` 표기) | ✅ |
| `memory/<loop_id>/` | 메모리 4종 + 스킬 메모리 | ✅ (클라우드 세션은 컨테이너가 사라지므로 커밋해야 기억이 남는다) |
| `runs/<loop_id>/<run_id>/` | `run.json` · `workers/` · `merged.json` · `report.json` · `attachments/` | ✅ |

> 민감정보 주의: 메모리와 실행 폴더는 커밋된다. 학생 개인정보(장애 진단명·연락처 등)는 원문으로 남기지 않는다 (`practicum-inquiry-triage`의 금지 사항).

## 5. 새 루프 추가

1. `loops/<새-loop-id>.json` 작성 (위 예시 2개 중 가까운 쪽을 복사).
2. `python3 loop-station/tools/loopcanon.py validate` 통과 확인.
3. 시간 기반이면 예약 작업(또는 n8n·cron)이 `due` → `start`를 부르도록 연결, 이벤트 기반이면 수신 쪽이 이벤트 JSON을 만들어 `match` → `start`를 부르도록 연결한다. (현재는 로컬 실행기까지 구현됨 — 실제 연결은 다음 단계)
