# Activity Tracker - 30분 활동 로깅 및 분석 앱

30분마다 질문과 선택을 통해 사용자의 일상 활동을 기록하고, AI 기반으로 분석하여 시간 관리 및 자기관리 인사이트를 제공하는 모바일 애플리케이션입니다.

## 프로젝트 구조

```
ai-class-workflow/
├── backend/               # FastAPI 백엔드
│   ├── app/
│   │   ├── models/       # SQLAlchemy 데이터베이스 모델
│   │   ├── routers/      # API 라우터
│   │   ├── schemas/      # Pydantic 스키마
│   │   ├── services/     # 비즈니스 로직
│   │   ├── config.py     # 설정
│   │   ├── database.py   # 데이터베이스 연결
│   │   └── main.py       # FastAPI 앱
│   ├── requirements.txt
│   ├── docker-compose.yml
│   └── .env
├── mobile/               # React Native 모바일 앱
│   ├── src/
│   │   ├── components/   # 재사용 가능한 컴포넌트
│   │   ├── screens/      # 화면 컴포넌트
│   │   ├── services/     # API 서비스
│   │   ├── contexts/     # React Context
│   │   └── navigation/   # 네비게이션 설정
│   ├── package.json
│   ├── app.json
│   └── App.js
└── ARCHITECTURE.md       # 아키텍처 문서
```

## 주요 기능

### 1. 활동 로깅
- 30분 주기 알림 시스템
- 활동 카테고리 선택 (work, study, exercise, leisure, etc.)
- 에너지 레벨 및 생산성 평가 (1-5 스케일)
- 기분 기록
- 위치 정보 자동 수집 (선택적)

### 2. 데이터 분석
- 카테고리별 시간 배분 분석
- 생산성 트렌드 추적
- 일일/주간/월간 통계
- 시각화 차트 (파이 차트, 바 차트)

### 3. 사용자 관리
- 회원가입/로그인 (JWT 인증)
- 알림 설정 관리
- 프로필 관리

### 4. 예정된 기능
- AI 기반 인사이트 및 개선 제안
- 위치 클러스터링 및 장소별 활동 분석
- 데이터 내보내기

## 기술 스택

### 백엔드
- **FastAPI** 0.104+ - 고성능 Python 웹 프레임워크
- **SQLAlchemy** 2.0+ - ORM
- **PostgreSQL** 15+ - 메인 데이터베이스
- **Redis** 7+ - 캐싱 및 세션 관리
- **JWT** - 인증
- **Pydantic** v2 - 데이터 검증

### 프론트엔드
- **React Native** 0.72+ - 크로스 플랫폼 모바일 앱
- **Expo** - 개발 플랫폼
- **React Navigation** - 네비게이션
- **React Native Paper** - UI 컴포넌트
- **Axios** - HTTP 클라이언트
- **AsyncStorage** - 로컬 저장소
- **Expo Notifications** - 푸시 알림
- **Expo Location** - 위치 서비스

## 설치 및 실행

### 사전 요구사항

- Python 3.10+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+
- Expo CLI (`npm install -g expo-cli`)

### 백엔드 설정

1. 데이터베이스 시작 (Docker 사용):
```bash
cd backend
docker-compose up -d
```

2. Python 가상환경 생성 및 활성화:
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. 의존성 설치:
```bash
pip install -r requirements.txt
```

4. 환경 변수 설정:
```bash
# .env 파일이 이미 생성되어 있습니다
# 필요시 SECRET_KEY와 OPENAI_API_KEY를 수정하세요
```

5. 서버 실행:
```bash
cd app
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API 문서: http://localhost:8000/docs

### 모바일 앱 설정

1. 의존성 설치:
```bash
cd mobile
npm install
```

2. API 베이스 URL 설정:
```bash
# src/services/api.js에서 API_BASE_URL을 수정
# 로컬 개발: http://localhost:8000/api/v1
# Android 에뮬레이터: http://10.0.2.2:8000/api/v1
# iOS 시뮬레이터: http://localhost:8000/api/v1
# 실제 기기: http://YOUR_COMPUTER_IP:8000/api/v1
```

3. 앱 실행:
```bash
# Expo 개발 서버 시작
npm start

# iOS 시뮬레이터에서 실행
npm run ios

# Android 에뮬레이터에서 실행
npm run android
```

## API 엔드포인트

### 인증
- `POST /api/v1/auth/register` - 회원가입
- `POST /api/v1/auth/login` - 로그인

### 사용자
- `GET /api/v1/users/me` - 내 정보 조회
- `PUT /api/v1/users/me` - 내 정보 수정

### 활동 로그
- `POST /api/v1/activities` - 활동 기록 생성
- `GET /api/v1/activities` - 활동 목록 조회 (페이징, 필터링)
- `GET /api/v1/activities/{id}` - 활동 상세 조회
- `PUT /api/v1/activities/{id}` - 활동 수정
- `DELETE /api/v1/activities/{id}` - 활동 삭제

## 데이터 모델

### User (사용자)
- 기본 정보: username, email, password_hash
- 설정: timezone, notification_enabled, notification_start_hour, notification_end_hour

### ActivityLog (활동 로그)
- 활동 정보: timestamp, activity_category, activity_detail, duration_minutes
- 평가: energy_level (1-5), productivity_rating (1-5), mood
- 노트: notes

### LocationContext (위치 컨텍스트)
- 위치 데이터: latitude, longitude, accuracy
- 메타데이터: location_name, address

### AnalysisReport (분석 리포트)
- 분석 결과: insights, recommendations, time_distribution, productivity_analysis

### LocationCluster (위치 클러스터)
- 클러스터 정보: cluster_name, center_latitude, center_longitude, radius_meters
- 통계: visit_count, total_time_minutes, primary_activity_category

## 개발 로드맵

### Phase 1 (완료) ✅
- [x] 백엔드 API 기본 구조
- [x] 데이터베이스 스키마
- [x] 사용자 인증
- [x] 활동 로그 CRUD
- [x] 30분 알림 기능
- [x] 기본 입력 폼
- [x] 위치 추적
- [x] 기본 시각화

### Phase 2 (진행 중) 🚧
- [ ] AI 분석 엔진 구현
- [ ] 위치 클러스터링
- [ ] 개인화 인사이트

### Phase 3 (계획) 📋
- [ ] 고급 시각화
- [ ] 리포트 내보내기
- [ ] 성능 최적화
- [ ] 백그라운드 작업 최적화

## 라이선스

MIT License

## 기여

기여를 환영합니다! Pull Request를 보내주세요.

## 문의

문제가 발생하면 GitHub Issues에 등록해주세요.