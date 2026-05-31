# 🧑‍🏫 특수체육 현장 교육실습 — 파이프라인 산출물

**파이프라인**: Scholar Gateway + PubMed (논문 수집) → Notion (실습 5영역 DB화) → n8n (역량진단·교수적합화 워크플로)
**생성일**: 2026-05-31

예비·현직 교사의 **특수체육 현장 교육실습(field practicum)** 을 지원하는 지식 베이스 + 자동화 워크플로입니다.
운동·근골격계 자가진단 앱([ai-workout PR #2](https://github.com/gw0777/ai-workout/pull/2))과 **병렬**로 제작된 대칭 구조이며,
이 저장소의 직접교수·개별화 지도모형 자료(`9장 직접교수_개별화 지도모형.pdf`)와 연계됩니다.

사전 키워드는 **최신 트렌드 + 미국·일본 연구 중심**:
- 🇺🇸 미국: Adapted Physical Education(APE), PETE, preservice practicum, self-efficacy(APAQ 저널), specially designed instruction
- 🇯🇵 일본: 특별지원교육, inclusive education teacher training, 패럴림픽 교육, para-sports practical sessions

---

## 1단계 — 논문 수집 (Scholar Gateway + PubMed)
- 총 **13편** 큐레이션 → [`evidence/evidence-library.csv`](evidence/evidence-library.csv)
- 지역 분포: 미국/서구 5 (APAQ 실습·자기효능감 핵심) · 일본 3 · 글로벌/리뷰 5
- 각 논문을 실습 5개 영역(①~⑤)에 매핑

## 2단계 — Notion 데이터베이스화
사용자 Notion 워크스페이스에 프로젝트 허브 + 2개 DB 생성:
- **프로젝트 허브**: https://www.notion.so/371f66a55e9381f48a23c8a460c6d214
- **📚 근거 논문 라이브러리 (Practicum Evidence)**: 13편
- **🧭 현장 교육실습 매뉴얼 (5개 영역)**: [`manual/practicum-manual.md`](manual/practicum-manual.md)와 동기화

## 3단계 — n8n 역량진단·교수적합화 워크플로
- 워크플로: https://aigw2026.app.n8n.cloud/workflow/Kp9XmZ2QrLs7VtN4
- 정의 export: [`n8n/ape-practicum-diagnosis.workflow.json`](n8n/ape-practicum-diagnosis.workflow.json)
- 구조 (12개 노드, 5영역 매핑):
  ```
  역량진단 폼(①) → Competency Engine(①②) → 주도지도?(≥65)(③) ─T→ 주도지도 적합화(③④) → 결과(⑤) → Data Table 기록
                                              └F→ 공동지도?(≥40)(③) ─T→ 공동지도 적합화(③④) → 결과(⑤) → 기록
                                                              └F→ 보조·관찰 배정(③④) → 결과(⑤) → 기록
  ```

### 준비도 컷오프 + 장애유형별 교수적합화
- **낮음 0–39(보조·관찰) / 중간 40–64(공동지도) / 높음 65–100(주도지도)** — 자가진단 앱과 동일한 65/40 컷오프
- 장애유형별 적합화 자동 분기: 자폐성장애·지적장애·지체장애·시각장애·청각장애
- 모든 결과는 n8n **Data Table**(`r3Wq8vTxY2mNpZ5K`)에 자동 기록 → 실습생 추이·코호트 분석

### 검증 결과 (실제 실행)
| 테스트 케이스 | 입력 | 준비도 | 판정 | 장애 적합화 | 기록 |
|---|---|---|---|---|---|
| 저준비 | 이해2·경험없음·효능감2 / 자폐 | 25 | 보조·관찰 ✅ | 구조화·시각단서 | id:1 ✅ |
| 고준비 | 이해5·여러번·효능감5 / 지적 | 90 | 주도지도 ✅ | 과제단순화·반복 | id:2 ✅ |

(execution #95·#96 — 모두 `success`, 장애유형별 적합화 정확 전환, Data Table 기록 누적 확인)

### 준비도 산출 로직 (영역①②)
- 5개 항목(장애이해·자기효능감·안전지식·의사소통·경험, 각 1–5점) → readiness = round((합계−5)/20×100)
- 결손 영역 자동 식별(gaps), 장애유형별 핵심 적합화 노트 생성 → ③④에서 역할·전략 추천

---

## 디렉터리 구조
```
special-pe-practicum/
├── README.md                              # 본 문서
├── evidence/
│   └── evidence-library.csv               # 근거 논문 13편
├── manual/
│   └── practicum-manual.md                # 현장 교육실습 5영역 매뉴얼
└── n8n/
    └── ape-practicum-diagnosis.workflow.json  # n8n 워크플로 정의 (import 가능)
```

> ⚠️ 본 산출물은 실습 지도·자기개발 참고용이며 공식 평가를 대체하지 않습니다.
> 준비도 가중치·컷오프(65/40)는 연구 기반 제안값이며, Data Table 누적 기록으로 현장 보정이 가능합니다.
