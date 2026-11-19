# 30분 활동 로깅 및 분석 앱 - 아키텍처 문서

## 프로젝트 개요
사용자의 일상 활동을 30분 간격으로 기록하고, AI 기반으로 분석하여 시간 관리 및 자기관리 인사이트를 제공하는 모바일 애플리케이션

## 기술 스택

### 프론트엔드 (모바일)
- **프레임워크**: React Native 0.72+
- **상태관리**: React Context API + AsyncStorage
- **UI 라이브러리**: React Native Paper
- **차트**: react-native-chart-kit
- **알림**: @react-native-community/push-notification-ios, react-native-push-notification
- **위치**: @react-native-community/geolocation
- **HTTP 클라이언트**: axios

### 백엔드
- **프레임워크**: FastAPI 0.104+
- **ORM**: SQLAlchemy 2.0+
- **인증**: JWT (python-jose)
- **검증**: Pydantic v2
- **CORS**: fastapi-cors
- **비동기**: asyncio, asyncpg

### 데이터베이스
- **메인 DB**: PostgreSQL 15+
  - 사용자 정보
  - 활동 로그
  - 위치 컨텍스트
- **캐시/세션**: Redis 7+
  - 세션 관리
  - API 캐싱

### AI/ML
- **LLM**: OpenAI GPT-4 API
- **분석 엔진**: Python scikit-learn
- **위치 클러스터링**: DBSCAN, K-means

## 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│                   Mobile App (React Native)              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Notification │  │ Input Form   │  │ Visualization│  │
│  │   Service    │  │  Component   │  │   Dashboard  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Location    │  │ Local Storage│  │ API Client   │  │
│  │   Tracker    │  │ (AsyncStorage│  │   (Axios)    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼ HTTPS/REST API
┌─────────────────────────────────────────────────────────┐
│                Backend API (FastAPI)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Auth       │  │   Activity   │  │   Location   │  │
│  │  Router      │  │    Router    │  │    Router    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Analysis   │  │   User       │  │ Notification │  │
│  │   Router     │  │   Router     │  │   Service    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                  Data Layer                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  PostgreSQL  │  │    Redis     │  │  OpenAI API  │  │
│  │   (Main DB)  │  │   (Cache)    │  │  (AI Engine) │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## 데이터 모델

### 1. User (사용자)
```python
- id: UUID (PK)
- username: String (unique)
- email: String (unique)
- password_hash: String
- created_at: DateTime
- timezone: String
- notification_enabled: Boolean
```

### 2. ActivityLog (활동 로그)
```python
- id: UUID (PK)
- user_id: UUID (FK -> User)
- timestamp: DateTime
- activity_category: String (work, study, exercise, leisure, etc.)
- activity_detail: String
- duration_minutes: Integer (default 30)
- energy_level: Integer (1-5)
- productivity_rating: Integer (1-5)
- notes: Text (optional)
- created_at: DateTime
```

### 3. LocationContext (위치 컨텍스트)
```python
- id: UUID (PK)
- activity_log_id: UUID (FK -> ActivityLog)
- latitude: Float
- longitude: Float
- location_name: String (optional, "Home", "Office", etc.)
- accuracy: Float
- address: String (optional)
- created_at: DateTime
```

### 4. UserInput (사용자 입력 기록)
```python
- id: UUID (PK)
- user_id: UUID (FK -> User)
- question_type: String (activity, location, mood, etc.)
- question_text: Text
- answer: JSON
- timestamp: DateTime
```

### 5. AnalysisReport (분석 리포트)
```python
- id: UUID (PK)
- user_id: UUID (FK -> User)
- report_type: String (daily, weekly, monthly)
- period_start: DateTime
- period_end: DateTime
- insights: JSON
- recommendations: JSON
- time_distribution: JSON
- created_at: DateTime
```

### 6. LocationCluster (위치 클러스터)
```python
- id: UUID (PK)
- user_id: UUID (FK -> User)
- cluster_name: String
- center_latitude: Float
- center_longitude: Float
- radius_meters: Float
- visit_count: Integer
- total_time_minutes: Integer
- created_at: DateTime
- updated_at: DateTime
```

## API 엔드포인트

### 인증
- `POST /api/v1/auth/register` - 회원가입
- `POST /api/v1/auth/login` - 로그인
- `POST /api/v1/auth/refresh` - 토큰 갱신

### 활동 로그
- `POST /api/v1/activities` - 활동 기록 생성
- `GET /api/v1/activities` - 활동 목록 조회 (필터링)
- `GET /api/v1/activities/{id}` - 활동 상세 조회
- `PUT /api/v1/activities/{id}` - 활동 수정
- `DELETE /api/v1/activities/{id}` - 활동 삭제

### 위치
- `POST /api/v1/locations` - 위치 기록 생성
- `GET /api/v1/locations/clusters` - 위치 클러스터 조회

### 분석
- `GET /api/v1/analysis/daily?date={date}` - 일일 분석
- `GET /api/v1/analysis/weekly?week={week}` - 주간 분석
- `GET /api/v1/analysis/insights` - AI 인사이트

### 사용자
- `GET /api/v1/users/me` - 내 정보 조회
- `PUT /api/v1/users/me` - 내 정보 수정
- `PUT /api/v1/users/me/settings` - 설정 변경

## 핵심 기능

### 1. 30분 주기 알림 시스템
- 로컬 푸시 알림 (백그라운드에서도 동작)
- 사용자 설정 가능한 활성 시간대
- 알림 건너뛰기 및 스누즈 기능

### 2. 활동 기록 인터페이스
- 선택형 카테고리 입력 (빠른 선택)
- 자유 텍스트 입력
- 에너지 레벨 및 생산성 평가
- 위치 자동 수집 (사용자 동의 시)

### 3. AI 기반 분석
- 시간 배분 패턴 분석
- 비효율적 시간 사용 식별
- 개인화된 개선 제안
- 생산성 트렌드 추적

### 4. 위치 기반 분석
- 자주 방문하는 장소 클러스터링
- 장소별 활동 패턴 분석
- 이동 시간 분석

### 5. 시각화 대시보드
- 일일/주간/월간 시간 배분 차트
- 카테고리별 시간 사용 비율
- 생산성 트렌드 그래프
- 위치 히트맵

## 보안 및 프라이버시

### 인증/인가
- JWT 기반 토큰 인증
- Access Token (15분) + Refresh Token (7일)
- 비밀번호 bcrypt 해싱

### 데이터 보호
- HTTPS 필수
- 민감한 데이터 암호화 저장
- 사용자 동의 기반 위치 수집
- GDPR 준수 데이터 삭제 기능

## 배포 전략

### 개발 환경
- Backend: Docker Compose (FastAPI + PostgreSQL + Redis)
- Mobile: Expo Dev Client / Android Studio

### 프로덕션
- Backend: AWS ECS / Google Cloud Run
- Database: AWS RDS PostgreSQL / Google Cloud SQL
- Cache: AWS ElastiCache / Google Memorystore
- Mobile: Google Play Store / Apple App Store

## 개발 우선순위

### Phase 1 (MVP)
1. 백엔드 API 기본 구조
2. 데이터베이스 스키마
3. 사용자 인증
4. 활동 로그 CRUD
5. 30분 알림 기능
6. 기본 입력 폼

### Phase 2
1. 위치 추적
2. 기본 시각화
3. 일일/주간 통계

### Phase 3
1. AI 분석 엔진
2. 위치 클러스터링
3. 개인화 인사이트

### Phase 4
1. 고급 시각화
2. 리포트 내보내기
3. 성능 최적화
