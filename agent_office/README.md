# agent_office — 디스코드 채널별 역할 봇 7개 하네스 (맥미니 24시간 서버용)

스레드(`1년 7개월차 연구교수의 AI 에이전트 진화 기록`)에서 소개된 구성을 **이 저장소가 이미 가진 일**
(특수체육 논문 파이프라인 `paper_pipeline_v2`, 유사도 검사 `similarity_checker`, 수업자료·제안서)에 맞게 옮긴 것입니다.

## 1. 스레드 내용 분석 → 설계 원칙

| 스레드에서 관찰된 것 | 여기서 구현한 방식 |
|---|---|
| 봇 7개: 매니저(총괄)·실장(연구)·조교(강의)·총무(학회)·팀장(센터)·작가(특강)·비서(개인업무) | `config/agents.yaml` 에 7역할 정의. 역할·채널·모델·도구·완료 기준을 한 곳에서 관리 |
| 디스코드에 업무마다 채널, 채널마다 담당 봇 → 맥락이 섞이지 않음 | 채널 이름 → 역할 라우팅(`office.py`). 토큰 7개면 봇 계정 7개, 토큰 1개면 계정 1개가 7채널 담당 |
| 필요 시 서로 정보 교환, 복잡한 일은 팀원 봇을 불러 나눠 맡김 | `delegate`(봇→봇 넘김), `spawn_subagent`(값싼 모델의 팀원 봇) |
| 메인봇은 최상위 모델, 서브에이전트는 특성에 맞게 모델을 달리해 비용 관리 | 메인 `claude-opus-5-5`(비서만 `claude-sonnet-5-5`), 팀원 `claude-haiku-5-5`. 역할별 **일일 토큰 예산** 초과 시 승인 전까지 정지 |
| 모든 작업은 최종적으로 본인 승인을 받는 가드레일 | `approval.py`: 파일 저장·메일 초안·논문 파이프라인 실행은 ✅/❌ 반응(또는 `!승인 N`)을 받기 전엔 실행 안 함 |
| (댓글) 봇 셋만 붙여도 누가 뭘 했는지 못 따라감 → 담당을 먼저 정한다 | 매니저가 **담당을 먼저 정해** 위임하고, 모든 메시지 앞에 역할 이름표 |
| (댓글) 넘기기 전에 한 일 한 줄 남기기 / '이렇게 되면 끝'을 한 줄로 적어두기 | 넘김 메시지에 `할 일 / 이렇게 되면 끝 / 한 일` 3줄 고정. 봇은 답변 끝에 `한 일: …` 필수 |
| (댓글) 봇끼리 주고받는 정보는 DM 말고 채널에 → '그때 왜 그렇게 판단했지' 검색 가능 | 넘김은 받는 봇의 채널에 공개 게시 + SQLite(`office.db`)의 `handoffs`/`events` 에 기록 |
| (댓글) 맥미니는 조용히 죽는 게 제일 무섭다 → launchd 자동 재시작 + 하루 1회 살아있음 알림 + 정전 후 자동 시작 | `deploy/launchd/com.agentoffice.plist`(KeepAlive) + `heartbeat.py`(매일 08시 KST `#사무실`) + `pmset autorestart` |
| 활동 상황을 보는 사무실 화면 | `dashboard.py`: 봇별 상태·토큰 사용률·승인 대기·최근 넘김·이벤트 (http://127.0.0.1:8787) |
| 너무 쪼개기만 하면 효율이 오르지 않음 → 업무 특성에 맞게 계속 조정 | 역할 추가·삭제·도구 변경이 YAML 수정만으로 끝나도록 설계 |

## 2. 역할과 채널

| 봇 | 채널 | 모델 / effort | 도구 | 이렇게 되면 끝 |
|---|---|---|---|---|
| 🧭 매니저(총괄) | `#매니저실`, `#사무실` | opus-5-5 / high | delegate, list_tasks, daily_briefing, spawn_subagent | 담당 채널에 완료 기준과 함께 넘어가고 한 줄 기록이 남음 |
| 📚 실장(연구) | `#연구실` | opus-5-5 / xhigh | run_paper_pipeline, similarity_check, write_file, spawn_subagent | 초안 DOCX + 유사도 리포트 + 참고문헌 검증 |
| 🏫 조교(강의) | `#강의실` | opus-5-5 / high | write_file, spawn_subagent | 주차별 목표·활동·평가가 있는 자료 저장 |
| 🎓 총무(학회) | `#학회` | opus-5-5 / high | write_file, send_email_draft | 마감일 기록 + 제출용 문서가 승인 대기 |
| 🏢 팀장(센터) | `#센터` | opus-5-5 / high | write_file, spawn_subagent | 목차·예산표·일정표 포함 문서 + 검토 포인트 3개 |
| ✍️ 작가(특강) | `#특강` | opus-5-5 / high | write_file | 분량·청중 명시 원고 + 슬라이드 개요 |
| 🗂️ 비서(개인업무) | `#비서실` | sonnet-5-5 / medium | send_email_draft, remind | 초안/리마인더 등록 + 확인 한 줄 |

- 용어 규칙: 모든 프롬프트·출력·저장 파일에서 **'적응체육'은 쓰지 않고 '특수체육'으로 통일**(`enforce_terms`).
- 메일은 **초안만** 저장하며 발송하지 않습니다. 논문 파이프라인 결과의 수치는 가상 수치입니다.

## 3. 설치

### 공통 준비
1. Discord 개발자 포털에서 봇 생성(계정 1개 또는 역할별 7개) → **Message Content Intent** 켜기 → 서버에 초대(권한: 메시지 보기/보내기, 반응 추가, 메시지 기록 읽기).
2. 서버에 텍스트 채널 생성: `매니저실 연구실 강의실 학회 센터 특강 비서실 사무실`.
3. 디스코드 설정 → 고급 → 개발자 모드 → 내 프로필 우클릭 → **ID 복사** = `OWNER_DISCORD_ID`.

### 맥미니(24시간 서버)
```bash
git clone https://github.com/gw0777/ai-class-workflow && cd ai-class-workflow
bash agent_office/deploy/install_macmini.sh     # venv + .env 생성 + launchd 등록 + pmset
# .env 를 채운 뒤:
launchctl kickstart -k gui/$(id -u)/com.agentoffice
tail -f agent_office/logs/agent_office.err.log
```
설치 스크립트는 ① 로그인 시 자동 시작·비정상 종료 시 10초 후 재시작(launchd KeepAlive), ② 정전 후 자동 시작·잠들지 않기(pmset)를 설정합니다.
시스템 설정 → 에너지 → **"정전 후 자동으로 시작"** 이 켜졌는지 한 번 확인하세요.

### 수동 실행 / 점검
```bash
cd agent_office && pip install -r requirements.txt && cp .env.example .env
python -m agent_office --check     # 토큰·소유자·채널·모델 점검
DRY_RUN=true python -m agent_office --cli   # API 호출 없이 터미널에서 배선 확인
python -m agent_office             # 봇 + 대시보드 + 하트비트 가동
```

## 4. 사용법
- 담당 채널에 그냥 말하면 그 봇이 처리합니다. 어디 맡길지 모르겠으면 `#매니저실`에 말하세요 → 매니저가 담당을 정해 넘깁니다.
- 승인 메시지(🔒)에 ✅ 또는 ❌ 반응. 대시보드에서도 승인/거부 가능. 명령: `!상태` `!할일` `!승인 N` `!거부 N`.
- 결과 파일은 `output/<역할>/` 에 저장됩니다. 실장이 만든 초안은 `similarity_check` 로 바로 유사도·참고문헌 검증이 가능합니다.
- `run_paper_pipeline` 을 쓰려면 `paper_pipeline_v2` 서버(`python mcp_server.py`, 기본 8000포트)가 떠 있어야 하고 `PAPER_PIPELINE_URL`/`PAPER_PIPELINE_API_KEY` 를 설정합니다.

## 5. 비용·안전 장치
| 장치 | 위치 | 기본값 |
|---|---|---|
| 역할별 일일 토큰 예산 | `defaults.daily_token_budget` / 역할별 override | 2,000,000 토큰. 초과 시 `budget_override` 승인 요청 |
| 승인 필요 도구 | `defaults.approval_required_tools` | run_paper_pipeline, write_file, send_email_draft, spawn_subagent |
| 승인 만료 | `APPROVAL_TIMEOUT_SEC` | 24시간(만료 시 실행 안 함) |
| 소유자 외 요청 | `ALLOW_NON_OWNER` | 무시 |
| 안전 정책 거절(refusal) 폴백 | `ENABLE_FALLBACKS` | opus/sonnet 5.5 계열에 서버측 `fallbacks="default"` 적용, 최종 거절은 채널에 사유 표시 |
| 프롬프트 캐싱 | `llm.py` | 시스템 프롬프트에 `cache_control` 브레이크포인트 |

## 6. 파일 구조
```
agent_office/
├── config/agents.yaml        # 7역할 정의(채널·모델·도구·완료 기준·예산)
├── agent_office/
│   ├── config.py             # 설정 로딩 + 용어 통일(enforce_terms)
│   ├── office.py             # 채널 라우팅·넘김·명령
│   ├── agent.py              # 역할 봇 루프(도구 호출, 승인, 한 줄 기록)
│   ├── tools.py              # delegate / spawn_subagent / run_paper_pipeline / similarity_check / write_file / ...
│   ├── approval.py           # ✅/❌ 승인 게이트
│   ├── memory.py             # SQLite 기록부(tasks, handoffs, approvals, usage, events, reminders, drafts)
│   ├── llm.py                # Anthropic SDK 래퍼(adaptive thinking, effort, 폴백) + Fake/Echo
│   ├── heartbeat.py          # 살아있음 알림·상태 요약·리마인더
│   ├── dashboard.py          # 사무실 화면(FastAPI)
│   ├── bot.py                # discord.py 봇 무리
│   └── main.py               # 진입점(--check / --cli / 전체)
├── deploy/launchd/com.agentoffice.plist, deploy/install_macmini.sh
├── tests/                    # 21개 (네트워크·디스코드 불필요)
└── requirements.txt, .env.example
```

## 7. 테스트
```bash
cd agent_office && python -m pytest -q tests && ruff check agent_office tests
```

## 8. 다음에 조정할 것(스레드 ③·역할 특성)
- 역할을 더 쪼개기 전에 2주 정도 `handoffs` 표를 보고 "넘김이 잦은 쌍"만 분리하세요(쪼개기만으로 효율이 오르지 않음).
- 가계부 봇처럼 숫자를 다루는 역할(센터 예산)은 월말에 원본 합계와 0원 차이인지 대조하는 체크리스트를 `done_criteria` 에 넣으세요.
