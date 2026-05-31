# 논문생산 파이프라인 v2 (구독 SaaS)

한국특수체육학회지 게재 수준의 **구조방정식모형(SEM) 논문**을 자동으로 생성하는 무인 파이프라인 +
**구독 기반 수익화** 인프라입니다. Gemini(학술/동향 검색) + Claude(설계·생성·교정·평가)를 결합하고,
품질 GATE를 통과할 때까지 자동 재생성합니다. **FastAPI + MCP SDK**로 구현되어 n8n 등 외부 도구와 HTTP로 연동됩니다.

## 핵심 특징
- **병렬 처리**: `asyncio.gather()`로 Stage 1 세 작업 동시 실행(Gemini 학술‖동향‖Claude 사전검증)
- **품질 GATE**: 10항목×0~10점(총 100), 70점 이상이면 통과·저장 / 미통과 시 Stage 4로 회귀
- **SEM 규칙 내장**: N=274, 잠재변수 7개, p값 선행 0 제거, APA 표 캡션 좌상단, 적합도 지수 보고
- **DOCX 내보내기**: `md_to_docx.py`(표지·바탕체·영문초록 자리·참고문헌 내어쓰기)
- **구독 SaaS 수익화**: API 키 인증 + 사용량 미터링 + 월간 한도 + Stripe 웹훅

## 파이프라인 단계
| 단계 | 내용 |
|------|------|
| Stage 1 (병렬) | Gemini 학술검색 ‖ Gemini 동향검색 ‖ Claude 참고문헌 사전검증 |
| Stage 2 | 참고문헌 중복제거 + APA 7th 정규화 |
| Stage 3 | Claude Researcher — 근거구조(연구문제/가설/7잠재변수) |
| Stage 4 | Claude Generator — SEM 논문 초안 |
| Stage 5 | Claude Proofreader — 7항목 교정 |
| Stage 6 | Claude Evaluator — 10항목 채점, 70+ GATE |
| Stage 7 | 통과 시 저장 / 미통과 시 Stage 4 회귀 |

## 파일 구조
```
paper_pipeline_v2/
├── mcp_server.py     # MCP 서버 + FastAPI REST + 수익화(인증/한도/미터링)
├── pipeline.py       # 7단계 파이프라인 + Gemini/Claude 클라이언트
├── billing.py        # 구독/사용량/한도/Stripe 웹훅 (SQLite)
├── models.py         # Pydantic 데이터 모델
├── md_to_docx.py     # Markdown → DOCX 변환기
├── tests/            # 단위 테스트(helpers, billing)
├── Dockerfile / .dockerignore / DEPLOY.md   # 배포
├── .env.example / requirements.txt
└── README.md / MONETIZATION.md
```

## 설치 & 실행
```bash
cd paper_pipeline_v2
pip install -r requirements.txt
cp .env.example .env       # GEMINI_API_KEY, CLAUDE_API_KEY 입력
python mcp_server.py        # http://localhost:8000
```

## 수익화 전략 (요약)
자세한 분석은 [`MONETIZATION.md`](./MONETIZATION.md) 참고. 인기 SaaS 10종(Notion AI, ChatGPT Plus,
GitHub Copilot, Perplexity Pro, Midjourney, Jasper, Copy.ai, Grammarly, Otter.ai, Canva AI)의
공통 패턴—**Freemium 한도 깔대기 + 워크플로 내재화 + 데이터 락인 + 변동비 연동 과금**—을
본 서비스에 적용했습니다.

### 가격표
| 플랜 | 가격 | 월 논문 한도 | 핵심 혜택 |
|------|------|------------|----------|
| **Free** | $0 | **3편/월** | DOCX 내보내기, 구글검색 문헌 수집 |
| **Pro** | **$29/월** | **무제한** | 우선 처리, 생성 이력 보관·재다운로드, 이메일 지원 |
| **Enterprise** | 문의 | 무제한 + 팀 | 온프레미스 라이선스, SSO, 감사로그, SLA |

### 수익화 API 사용법
```bash
# 1) API 키 발급
curl -X POST http://localhost:8000/api/signup -H "Content-Type: application/json" -d '{"email":"you@example.com"}'
#  -> {"api_key":"ppk_...", "plan":"free", "quota":{...}}

# 2) 플랜 조회(공개)
curl http://localhost:8000/api/plans

# 3) 사용량 조회(인증)
curl http://localhost:8000/api/usage -H "X-API-Key: ppk_..."

# 4) 논문 생성(인증 + 한도 적용)
curl -X POST http://localhost:8000/api/pipeline/run \
  -H "X-API-Key: ppk_..." -H "Content-Type: application/json" \
  -d '{"topic":"...","max_iterations":3,"gate_threshold":70}'
#  Free 한도 초과 시 HTTP 402 (Pro 업그레이드 안내)
```
> `BILLING_ENABLED=false` 로 두면 인증/한도 없이 개발 모드로 동작합니다.

## REST 엔드포인트
| 메서드 | 경로 | 인증 | 설명 |
|--------|------|:----:|------|
| GET | `/health` | — | 상태/버전/과금 활성여부 |
| GET | `/api/plans` | — | 구독 플랜 카탈로그 |
| POST | `/api/signup` | — | API 키 발급 |
| GET | `/api/usage` | ✅ | 내 플랜·사용량·잔여 한도 |
| POST | `/api/pipeline/run` | ✅ | 전체 파이프라인(한도 적용) |
| POST | `/api/stage1`~`/api/stage6` | ✅ | 단계별 실행 |
| POST | `/webhooks/stripe` | 서명 | Stripe 결제 이벤트 |

## 환경변수(수익화 관련)
| 변수 | 기본 | 설명 |
|------|------|------|
| `BILLING_ENABLED` | `true` | 인증/한도 적용 여부 |
| `SIGNUP_OPEN` | `true` | `/api/signup` 공개 가입 허용 |
| `BILLING_DB` | `billing.db` | SQLite 경로 |
| `STRIPE_WEBHOOK_SECRET` | — | 설정 시 웹훅 서명 검증(미설정 시 개발용 JSON 파싱) |
| `STRIPE_PRICE_PRO` / `STRIPE_PRICE_ENTERPRISE` | — | price_id → plan 매핑 |

## 로드맵
- [x] 수익화 토대(인증 + 사용량 미터링 + 월간 한도 + /usage, /plans)
- [x] Stripe 웹훅 기본 구조
- [x] Docker/배포 가이드 + CI
- [ ] Stripe Checkout 세션 생성(결제 페이지)
- [ ] 대시보드/랜딩 UI
- [ ] 비동기 작업큐(생성 ID + 상태 조회)
- [ ] 종량제 크레딧 하이브리드, 팀 좌석·SSO(Enterprise)

## 주의
- 생성 논문의 데이터·통계·인용은 LLM이 생성한 **가상 수치**입니다. 실제 게재 전 반드시 실측 데이터로 교체·검증하세요.
- API 키·결제 시크릿은 `.env`/플랫폼 시크릿으로만 주입하고 저장소에 커밋하지 마세요(`.gitignore` 포함).
