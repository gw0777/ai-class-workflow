# CLAUDE.md — 작업 규칙

## 순차 실행 원칙 (CRITICAL)

**생성과 동시에 그 결과 ID를 참조하는 작업을 한 배치(병렬)에 넣지 말 것.**

의존 관계가 있는 작업은 반드시 순차 실행:

1. 리소스 생성 (n8n workflow, Notion DB, Data Table 등)
2. 응답에서 실제 ID 확인
3. 그 ID를 다음 단계에서 사용

### 잘못된 패턴 (금지)

```
# 같은 배치에서 — 절대 안 됨
create_workflow(...)          # → 워크플로 생성
update_notion(id="추측값")   # → ID를 모르는 상태에서 참조
```

### 올바른 패턴

```
# 1단계
result = create_workflow(...)
actual_id = result.id        # 응답에서 실제 ID 추출

# 2단계 (1단계 완료 후)
update_notion(id=actual_id)  # 실제 ID 사용
```

### 적용 범위

- n8n 워크플로 생성 → 그 ID로 README/Notion 업데이트
- n8n Data Table 생성 → 그 ID를 워크플로 코드에 삽입
- Notion DB 생성 → 그 collection_id로 페이지 추가
- GitHub PR 생성 → 그 번호로 README 링크 추가

---

## 프로젝트 개요

**특수체육 현장 교육실습 지원** — `special-pe-practicum/` 디렉터리

파이프라인: Scholar Gateway + PubMed (논문 수집) → Notion (5영역 DB화) → n8n (역량진단·교수적합화 워크플로)

### 핵심 파라미터

- 준비도 컷오프: **65점**(주도지도) / **40점**(공동지도) — ai-workout과 동일한 65/40 기준
- 장애유형별 자동 분기: 자폐성장애 / 지적장애 / 지체장애 / 시각장애 / 청각장애
- n8n 워크플로 ID: `GShLyUWZH8rMcPVt`
- n8n Data Table ID: `s7lc68owevdCH6wV`

### 브랜치

개발 브랜치: `claude/serene-goodall-6gQyH`
