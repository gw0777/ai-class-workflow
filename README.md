# 범용 정책 분석 플랫폼 (Universal Policy Analysis Platform)

6계층 아키텍처 기반의 범용 정책 분석 시스템입니다. 장애인 체육 정책뿐만 아니라 교육, 의료, 환경, 과학기술 등 다양한 분야의 정책을 분석할 수 있는 확장 가능한 플랫폼입니다.

## 🏗️ 시스템 아키텍처: 6계층 구조

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 6: 프론트엔드 (React + Vite + Tailwind CSS)           │
│  - 직관적인 검색 인터페이스                                    │
│  - 프롬프트 생성 & 최적화 도구                                 │
│  - 실시간 분석 결과 시각화                                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 5: API 레이어 (Express.js + TypeScript)              │
│  - RESTful API 엔드포인트                                     │
│  - 요청 검증 & 에러 핸들링                                    │
│  - Rate Limiting & 보안                                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 4: AI 분석 레이어 (Claude API + RAG)                  │
│  - RAG 파이프라인 (검색 + 생성)                               │
│  - Prompt Caching (비용 90% 절감)                            │
│  - Haiku/Sonnet 모델 선택 전략                               │
│  - 정책 비교 & 트렌드 분석                                    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: NLP 처리 레이어 (Natural Language Processing)     │
│  - 한국어 형태소 분석 & 토큰화                                │
│  - TF-IDF 키워드 추출                                         │
│  - 텍스트 청킹 (512 토큰, 50 오버랩)                         │
│  - Named Entity Recognition (NER)                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: 데이터 저장 레이어 (Hybrid Database)               │
│  ┌──────────────┬─────────────────┬──────────────────────┐  │
│  │ PostgreSQL   │ MongoDB         │ Qdrant (Vector DB)   │  │
│  │ - 메타데이터 │ - 문서 원문     │ - 임베딩 벡터         │  │
│  │ - 구조화     │ - 비구조화      │ - 의미 검색           │  │
│  └──────────────┴─────────────────┴──────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: 데이터 수집 레이어 (Web Crawling)                  │
│  - 범용 크롤러 (정적/동적 페이지)                             │
│  - 주제별 어댑터 패턴                                         │
│  - PDF/HWP 문서 파싱                                          │
│  - Open API 통합                                              │
└─────────────────────────────────────────────────────────────┘
```

## ✨ 핵심 기능

### 1. 다중 주제 지원
- **장애인 체육**: 생활체육, 전문체육, 반다비 센터, 패럴림픽
- **교육 정책**: 교육과정, 평가 제도, 입시 정책
- **보건의료**: 건강보험, 공중보건, 의료기관 관리
- **환경 정책**: 기후변화, 탄소중립, 친환경 에너지
- **과학기술**: R&D, 디지털 전환, AI/ICT 정책
- **커스텀 주제**: AI 기반 자동 템플릿 생성

### 2. AI 정책 분석 (Claude API + RAG)
- **의미 기반 검색**: Vector DB를 활용한 유사 문서 검색
- **정확한 답변 생성**: 검색된 문서를 기반으로 Claude가 답변
- **출처 명시**: 모든 답변에 참고 문서 자동 표시
- **비용 최적화**: Prompt Caching으로 90% 비용 절감

### 3. 프롬프트 생성 & 최적화
- **자동 평가**: 프롬프트 품질 점수 (0-100점)
- **AI 개선**: Claude가 프롬프트를 자동으로 개선
- **템플릿 제공**: 정책 요약, 비교, 트렌드 분석 템플릿

### 4. 하이브리드 데이터베이스
- **PostgreSQL**: 정확한 필터링 (날짜, 발행기관, 문서유형)
- **MongoDB**: 대용량 문서 원문 저장
- **Qdrant**: 코사인 유사도 기반 벡터 검색

## 🚀 빠른 시작

### 필수 요구사항
- Node.js 18+
- PostgreSQL 14+
- MongoDB 6+
- Qdrant (Docker 권장)
- Claude API Key (Anthropic)

### 1. 저장소 클론
```bash
git clone <repository-url>
cd ai-class-workflow
```

### 2. 데이터베이스 설정

#### PostgreSQL
```bash
# PostgreSQL 설치 (Ubuntu/Debian)
sudo apt-get install postgresql postgresql-contrib

# 데이터베이스 생성
sudo -u postgres createdb policy_analysis

# 스키마 적용
psql -U postgres -d policy_analysis -f backend/src/db/schema.sql
```

#### MongoDB
```bash
# MongoDB 설치
sudo apt-get install mongodb
sudo systemctl start mongodb
```

#### Qdrant (Docker)
```bash
docker run -d -p 6333:6333 qdrant/qdrant:latest
```

### 3. 환경 변수 설정

```bash
cd backend
cp .env.example .env
# .env 파일을 편집하여 API 키와 DB 연결 정보 입력
```

### 4. 백엔드 실행
```bash
cd backend
npm install
npm run dev
```

### 5. 프론트엔드 실행
```bash
cd frontend
npm install
npm run dev
```

### 6. 전체 실행 (루트에서)
```bash
npm install
npm run dev
```

## 📁 프로젝트 구조

```
ai-class-workflow/
├── backend/                 # Express.js 백엔드
│   ├── src/
│   │   ├── config/         # 데이터베이스 설정
│   │   ├── services/       # 비즈니스 로직
│   │   │   ├── crawler/    # 웹 크롤링
│   │   │   ├── nlp/        # NLP 처리
│   │   │   ├── vector/     # Vector DB
│   │   │   ├── claude/     # Claude API + RAG
│   │   │   └── template/   # 주제 템플릿
│   │   ├── routes/         # API 라우트
│   │   └── server.ts       # Express 서버
│   └── package.json
│
├── frontend/               # React 프론트엔드
│   ├── src/
│   │   ├── components/    # React 컴포넌트
│   │   ├── api/           # API 클라이언트
│   │   └── App.tsx        # 메인 앱
│   └── package.json
│
└── README.md
```

## 🔧 API 엔드포인트

### 템플릿 API
- `GET /api/templates` - 모든 주제 템플릿
- `POST /api/templates/create` - 새 템플릿 생성

### RAG API
- `POST /api/rag/query` - RAG 쿼리 실행
- `POST /api/rag/compare` - 정책 비교
- `POST /api/rag/prompt/evaluate` - 프롬프트 평가
- `POST /api/rag/prompt/improve` - 프롬프트 개선

## 💡 사용 예시

```bash
# RAG 쿼리 예시
curl -X POST http://localhost:5000/api/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "2024년 장애인 생활체육 참여율은?",
    "topicName": "disability_sports",
    "model": "sonnet"
  }'
```

## 🎯 비용 최적화

- **Prompt Caching**: 90% 비용 절감
- **모델 선택**: Haiku (간단) vs Sonnet (복잡)
- **1,000회 쿼리 기준**: $1.5-2 (캐시 사용 시)

## 📚 기술 스택

- **Frontend**: React, Vite, Tailwind CSS, TypeScript
- **Backend**: Express.js, TypeScript, Node.js
- **Database**: PostgreSQL, MongoDB, Qdrant
- **AI**: Claude API (Anthropic)
- **NLP**: Natural, Stopword, TF-IDF
- **Crawling**: Axios, Cheerio, Puppeteer

## 📄 라이선스

MIT License

---

**Built with Claude API**