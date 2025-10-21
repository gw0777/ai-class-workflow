# 교수-학생 AI 소통 플랫폼

AI 기반 메시지 분석을 통해 교수와 학생 간의 효과적이고 명확한 소통을 지원하는 웹 어플리케이션입니다.

## 주요 기능

### 핵심 가치
- **감정 배제**: AI가 교수의 메시지에서 감정적 표현을 감지하고 중립적으로 변환
- **오해 방지**: 메시지의 모호한 표현과 오해의 소지를 분석하여 개선 제안
- **명확한 소통**: 전문적이고 명확한 메시지로 재구성하여 학생들의 이해도 향상
- **사전 검증**: 단체 메시지 전송 전 AI 상담을 통해 특정 학생에 대한 편향 방지

### 교수 기능
1. **AI 메시지 분석**
   - 작성한 메시지의 감정 분석
   - 오해 위험도 평가 (낮음/보통/높음)
   - 문제점 자동 감지 및 표시
   - 개선된 메시지 자동 생성

2. **메시지 작성 워크플로우**
   - 1단계: 수신자 선택 (개별 학생 또는 그룹)
   - 2단계: 메시지 작성
   - 3단계: AI 분석 결과 확인 및 메시지 수정
   - 4단계: 최종 확인 및 전송

3. **그룹 관리**
   - 학생 그룹 생성 및 관리
   - 그룹별 멤버 추가/제거
   - 그룹 단위 메시지 전송

### 학생 기능
1. **메시지 수신**
   - 교수로부터 받은 메시지 조회
   - 읽지 않은 메시지 알림
   - 메시지 읽음 표시 자동 처리

2. **피드백 제공**
   - 메시지에 대한 반응 등록 (도움됨/명확함/혼란스러움)

## 기술 스택

### Backend
- **Node.js** + **Express**: RESTful API 서버
- **SQLite**: 경량 데이터베이스
- **JWT**: 인증 및 세션 관리
- **Anthropic Claude API**: AI 메시지 분석 엔진

### Frontend
- **React 18**: 사용자 인터페이스
- **Vite**: 빠른 개발 환경
- **React Router**: 페이지 라우팅
- **Axios**: API 통신

## 빠른 시작

### 사전 요구사항
- Node.js 18 이상
- Anthropic API 키 ([https://console.anthropic.com/](https://console.anthropic.com/)에서 발급)

### 설치 및 실행

#### 1. Backend 설정
```bash
cd backend
npm install

# .env 파일 수정하여 API 키 설정
# ANTHROPIC_API_KEY=your-api-key-here

npm start
```

#### 2. Frontend 설정
```bash
cd frontend
npm install
npm run dev
```

#### 3. 브라우저에서 접속
`http://localhost:5173`으로 접속하세요.

상세한 설치 가이드는 [SETUP_GUIDE.md](./SETUP_GUIDE.md)를 참조하세요.

## 프로젝트 구조

```
ai-class-workflow/
├── backend/                  # Node.js 백엔드 서버
│   ├── src/
│   │   ├── controllers/     # 비즈니스 로직
│   │   ├── models/          # 데이터베이스 모델
│   │   ├── routes/          # API 라우트
│   │   ├── services/        # AI 서비스
│   │   ├── middleware/      # 인증 미들웨어
│   │   └── server.js        # 서버 진입점
│   └── package.json
├── frontend/                 # React 프론트엔드
│   ├── src/
│   │   ├── components/      # 재사용 가능한 컴포넌트
│   │   ├── pages/           # 페이지 컴포넌트
│   │   ├── contexts/        # React Context (인증 등)
│   │   ├── services/        # API 클라이언트
│   │   └── App.jsx          # 메인 앱 컴포넌트
│   └── package.json
├── SETUP_GUIDE.md           # 상세 설치 가이드
└── README.md                # 이 파일
```

## 데모 시나리오

### 교수가 메시지를 작성할 때

**원본 메시지:**
```
이번 과제를 제출하지 않은 학생들이 너무 많습니다.
정말 실망스럽네요. 다음에는 꼭 제출하세요!
```

**AI 분석 결과:**
- 감정 분석: 실망, 부정적
- 위험도: **높음**
- 문제점:
  - "너무 많습니다" - 단체 메시지에서 일부 학생 겨냥
  - "정말 실망스럽네요" - 감정적 표현
  - "꼭 제출하세요!" - 명령조

**개선된 메시지:**
```
과제 제출 기한 안내

이번 과제 제출 기한이 지났습니다.
아직 제출하지 않은 학생들은 다음 기한까지 제출해 주시기 바랍니다.

제출 관련 문의사항이 있으시면 언제든 연락 주세요.
```

## API 문서

주요 API 엔드포인트:

### 인증
- `POST /api/auth/register` - 회원가입
- `POST /api/auth/login` - 로그인
- `GET /api/auth/me` - 현재 사용자 정보

### 메시지
- `POST /api/messages/analyze` - 메시지 AI 분석
- `POST /api/messages/draft` - 메시지 초안 생성
- `POST /api/messages/:id/send` - 메시지 전송
- `GET /api/messages/sent` - 전송한 메시지 목록
- `GET /api/messages/received` - 받은 메시지 목록

### 그룹
- `POST /api/groups` - 그룹 생성
- `GET /api/groups` - 그룹 목록
- `GET /api/groups/:id` - 그룹 상세 정보
- `POST /api/groups/:id/students` - 학생 추가
- `DELETE /api/groups/:id` - 그룹 삭제

## 기여

이슈와 풀 리퀘스트는 언제나 환영합니다!

## 라이선스

MIT License