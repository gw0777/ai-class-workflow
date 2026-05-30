# 논문생산 무인 파이프라인 v2

한국특수체육학회지 게재 수준의 **구조방정식모형(SEM) 논문**을 자동으로 생산하는 무인 파이프라인입니다.
Gemini(학술/동향 검색) + Claude(연구설계·생성·교정·평가)를 결합하고, 품질 GATE를 통과할 때까지
자동으로 재생성합니다. **FastAPI + MCP SDK** 로 구현되어 n8n 등 외부 자동화 도구와 HTTP로 연동됩니다.

## 핵심 특징

- **병렬 처리**: `asyncio.gather()` 로 Stage 1의 세 작업을 동시에 실행
  - Gemini 학술검색 ‖ Gemini 동향검색 ‖ Claude 참고문헌 사전검증
- **품질 GATE**: 10개 항목 × 0~10점(총 100점), **총점 70점 이상**이면 통과·저장,
  미통과 시 평가 피드백을 반영해 **Stage 4(생성)로 회귀**(최대 N회)
- **SEM 논문 규칙 내장**: 표본 `N=274`, 잠재변수 **정확히 7개**, **p값 선행 0 제거**(예: `p < .001`),
  **APA 표 캡션 좌상단**, 적합도 지수(χ²/CFI/TLI/RMSEA/SRMR) 보고
- **이중 인터페이스**: 각 Stage를 **MCP tool** 로 노출 + n8n용 **REST endpoint** 제공
- **Claude 모범 사례**: `claude-opus-4-8`, adaptive thinking, 프롬프트 캐싱, 스트리밍

## 파이프라인 단계

| 단계 | 내용 |
|------|------|
| **Stage 1** (병렬) | Gemini 학술검색 ‖ Gemini 동향검색 ‖ Claude 참고문헌 사전검증 |
| **Stage 2** | 참고문헌 중복제거 + APA 7th 인용 정규화 |
| **Stage 3** | Claude Researcher — 근거구조(연구문제/가설/7잠재변수/측정·구조모형) |
| **Stage 4** | Claude Generator — SEM 논문 초안 (N=274, 7잠재변수, p값 선행0, APA 표) |
| **Stage 5** | Claude Proofreader — 7항목 교정 |
| **Stage 6** | Claude Evaluator — 10항목 0~10점 채점, 총점 70+ GATE |
| **Stage 7** | GATE 통과 시 결과 저장 / 미통과 시 Stage 4 회귀 |

## 파일 구조

```
paper_pipeline_v2/
├── mcp_server.py     # 메인: MCP 서버 + FastAPI REST
├── pipeline.py       # 파이프라인 로직 + Gemini/Claude 클라이언트
├── models.py         # Pydantic 데이터 모델
├── .env.example      # 환경변수 예시
├── requirements.txt  # 의존성
└── README.md         # 본 문서
```

## 설치 & 실행

```bash
cd paper_pipeline_v2

# 1) 가상환경(선택) 후 의존성 설치
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2) 환경변수 설정
cp .env.example .env
#  .env 를 열어 GEMINI_API_KEY, CLAUDE_API_KEY 입력

# 3) 서버 실행
python mcp_server.py
#  또는: uvicorn mcp_server:app --host 0.0.0.0 --port 8000
```

서버가 뜨면:

- 헬스체크: `GET http://localhost:8000/health`
- REST(n8n용): `POST http://localhost:8000/api/pipeline/run`
- MCP(스트리밍 HTTP): `http://localhost:8000/mcp`

### 빠른 테스트 (curl)

```bash
curl -X POST http://localhost:8000/api/pipeline/run \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "지적장애 학생의 신체활동 참여와 삶의 질",
    "keywords": ["특수체육", "삶의 질", "자기효능감"],
    "max_iterations": 3,
    "gate_threshold": 70
  }'
```

응답에는 단계별 결과, 최종 논문(`final_paper.body_markdown`), 평가 점수(`evaluation`),
GATE 통과 여부(`passed`), 저장 경로(`saved_path`)가 포함됩니다.

## REST 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET  | `/health` | 상태/키 설정 확인 |
| POST | `/api/pipeline/run` | 전체 파이프라인 실행 (메인) |
| POST | `/api/stage1` | Stage 1 단독 — `{topic, keywords}` |
| POST | `/api/stage2` | Stage 2 단독 — `{stage1}` |
| POST | `/api/stage3` | Stage 3 단독 — `{topic, stage1, stage2}` |
| POST | `/api/stage4` | Stage 4 단독 — `{topic, evidence, stage2, iteration, feedback}` |
| POST | `/api/stage5` | Stage 5 단독 — `{markdown}` |
| POST | `/api/stage6` | Stage 6 단독 — `{markdown, gate_threshold}` |

## n8n 연동 방법

### 방법 A — HTTP Request 노드 (가장 간단, 권장)

1. n8n에서 **HTTP Request** 노드를 추가합니다.
2. 설정:
   - **Method**: `POST`
   - **URL**: `http://<서버주소>:8000/api/pipeline/run`
   - **Body Content Type**: `JSON`
   - **Body**:
     ```json
     {
       "topic": "{{ $json.topic }}",
       "keywords": {{ $json.keywords }},
       "max_iterations": 3,
       "gate_threshold": 70
     }
     ```
3. 실행하면 응답 JSON의 `final_paper.body_markdown`(논문 본문), `evaluation.total`(총점),
   `passed`(통과 여부)를 다음 노드(노션 저장, 이메일 등)로 연결하세요.

> 논문 1편 생성은 LLM 호출이 많아 시간이 걸립니다. n8n HTTP Request 노드의
> **Timeout** 값을 넉넉히(예: 600000ms) 설정하세요.

### 방법 B — MCP Client 노드

n8n의 **MCP Client** 노드(또는 AI Agent의 MCP 도구)에서 MCP 서버 URL을
`http://<서버주소>:8000/mcp` (Streamable HTTP) 로 등록하면 다음 도구를 사용할 수 있습니다.

- `run_full_pipeline` — 전체 실행
- `stage1_parallel_search` ~ `stage6_evaluator` — 단계별 실행

## 환경변수

| 변수 | 필수 | 기본값 | 설명 |
|------|:----:|--------|------|
| `GEMINI_API_KEY` | ✅ | — | Google Gemini API 키 |
| `CLAUDE_API_KEY` | ✅ | — | Anthropic Claude API 키 |
| `CLAUDE_MODEL` | | `claude-opus-4-8` | Claude 모델 |
| `GEMINI_MODEL` | | `gemini-2.5-flash` | Gemini 모델 |
| `CLAUDE_EFFORT` | | `high` | 추론 강도(low/medium/high/xhigh/max) |
| `OUTPUT_DIR` | | `output` | GATE 통과 결과 저장 폴더 |
| `GEMINI_TIMEOUT` / `CLAUDE_TIMEOUT` | | `120` / `600` | 호출 타임아웃(초) |
| `HOST` / `PORT` | | `0.0.0.0` / `8000` | 서버 바인딩 |

## 주의

- 본 시스템은 **연구 보조용 초안 생성기**입니다. 생성된 논문의 데이터·통계·인용은
  반드시 연구자가 실제 데이터와 대조하여 검증해야 합니다. (LLM은 수치를 그럴듯하게
  생성할 수 있으므로 결과/표는 실제 분석 결과로 교체하세요.)
- API 키는 `.env` 에만 두고 절대 저장소에 커밋하지 마세요.
