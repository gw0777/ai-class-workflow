# ai-class-workflow

교육 업무를 위한 AI 워크플로우 저장소. 두 개의 독립 시스템과 교육 자료 아카이브로 구성된다.

## 구성

| 경로 | 내용 |
|---|---|
| [`agent.md`](agent.md) | **에이전트 운영 규약** — AI 에이전트가 산출물 제작 시 따르는 품질 프로토콜 |
| [`loop-station/`](loop-station/) | **루프 스테이션** — 98/100점 게이트 품질 루프 + HTML 검수 보고서·기록 시스템 |
| `paper_pipeline_v2/` | 논문 생산 파이프라인 v2 (구독 SaaS, 별도 시스템 — 자체 README 참조) |
| `*.pdf`, `*.pptx` | 체육 교육 자료 아카이브 (협동학습, 직접교수·개별화 지도모형 등) |

## 에이전트 + 루프 스테이션 개요

```
사용자 요청
   ↓
① 요구 분석·유형 판별 (education | html_report | document | general)
   ↓
② 초안 제작 (자체 완결형 HTML 등)
   ↓
③ 루브릭 자체 채점 (감점 우선, 회전 1은 95점 상한)
   ↓
④ 98점 미만 → 최다 감점 항목부터 수정 → 재채점 (최대 5회전)
   ↓
⑤ 98점 이상 + 앵커 규칙(치명 0·중대 0·경미 ≤2) 통과
   ↓
⑥ 기록 JSON 저장 → 검수 보고서·대시보드 HTML 생성
```

## 빠른 시작

1. AI 에이전트에게 작업을 요청하면, 에이전트는 [`agent.md`](agent.md)의 프로토콜에 따라 초안 → 자체 채점 → 수정 루프를 거쳐 98점 이상 산출물만 제출한다.
2. 실행 기록은 `loop-station/records/`에 남고, 검수 보고서는 다음 명령으로 생성된다:
   ```bash
   python3 loop-station/tools/loopstation.py build
   ```
3. `loop-station/site/index.html`을 브라우저로 열면 전체 실행 이력 대시보드를 볼 수 있다.

자세한 스키마·도구 사용법은 [`loop-station/README.md`](loop-station/README.md) 참조.
