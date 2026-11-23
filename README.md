# ai-class-workflow

| 디렉터리 | 내용 |
|---|---|
| [`paper_pipeline_v2/`](./paper_pipeline_v2) | 논문생산 파이프라인 v2 (Gemini+Claude, FastAPI/MCP, 구독 SaaS) |
| [`similarity_checker/`](./similarity_checker) | 개인용 논문 유사도·표절 검사 도구 (카피킬러 대체: 로컬/GitHub 코퍼스, 참고문헌 실존 검증, HTML 리포트) |
| [`agent_office/`](./agent_office) | 디스코드 채널별 역할 봇 7개(매니저·실장·조교·총무·팀장·작가·비서) 하네스: 승인 가드레일, 넘김 기록, 맥미니 launchd 24시간 가동, 사무실 대시보드 |
| [`agent_system/`](./agent_system) | 교육 공동설계(co-design) 에이전트 시스템 |
| [`book-publishing-app/`](./book-publishing-app) | 도서 출판 앱 |
| [`loop-station/`](./loop-station) | 98점 품질 게이트 루프스테이션 + **루프 정석**(트리거·커넥터·메모리·서브에이전트·워크트리·스킬·사람 검토, [`LOOP_CANON.md`](./loop-station/LOOP_CANON.md)) (`agent.md` 참조) |
| [`special-pe-practicum/`](./special-pe-practicum) | 특수체육 실습 자료 |
| [`special_pe_visual_impairment/`](./special_pe_visual_impairment) | 시각장애 특수체육 자료 |
| [`claude-mods/`](./claude-mods) · [`reports/`](./reports) | Claude 모드 설정 및 리포트 (paper_pipeline_v2 파이프라인 개선과 함께 통합) |
| [`tournament-bracket.html`](./tournament-bracket.html) | 실시간 토너먼트 대진표 (`TOURNAMENT_README.md`) |
| [`projects/mobile-backend-app/`](./projects/mobile-backend-app) | 모바일 앱 + 백엔드 (주기 알림 기능 포함, 범용 폴더명 충돌 방지를 위해 projects/ 하위로 격리) |
| [`projects/professor-student-comm/`](./projects/professor-student-comm) | 교수–학생 소통 앱 (backend/frontend, `SETUP_GUIDE.md`·`따라하기_가이드.md`) |
| [`projects/music-impact-control/`](./projects/music-impact-control) | 음악 임팩트 컨트롤 웹앱 (app.js/index.html, projects/ 격리) |
| [`projects/pe-expert-app/`](./projects/pe-expert-app) | APA 체육 전문가 앱 (Python `apa_expert_app.py`, `run_app.sh/.bat`) |
| [`projects/presentation-support/`](./projects/presentation-support) | 프로젝트 발표 지원 Flask 앱 (`app.py`, static/templates) |
| [`projects/toss-payment/`](./projects/toss-payment) | 토스 결제 연동 (Firebase functions/frontend/firestore) |
| [`projects/disability-sports-policy/`](./projects/disability-sports-policy) | 장애인스포츠 정책 플랫폼 (backend/frontend, `TOPIC_GUIDE.md`) |

```bash
pip install -r similarity_checker/requirements.txt
python -m similarity_checker index add ./papers          # 비교 문헌 색인
python -m similarity_checker check 내논문.docx --out-dir reports --refs --online
```

```bash
# 디스코드 사무실(봇 7개) — 맥미니 24시간 서버
bash agent_office/deploy/install_macmini.sh            # venv + .env + launchd + pmset
cd agent_office && python -m agent_office --check      # 설정 점검
```

## 브랜치 통합 현황

루트를 서로 다른 앱으로 차지하던 브랜치 5종은 모두 `projects/` 하위로 격리 통합되었습니다(music-impact-control · pe-expert-app · presentation-support · toss-payment · disability-sports-policy). 남은 미통합 루트 앱 브랜치는 없습니다.

이미 통합된 브랜치에 **완전히 포함**되어 별도 병합이 불필요한 브랜치: `claude/agent-realtime-system-*` ⊂ `sports-management-motion-graphics` / `claude/add-periodic-notification-*` ⊂ `init-project`(→ `projects/mobile-backend-app/`). 원본 브랜치는 모두 보존되어 있습니다.
