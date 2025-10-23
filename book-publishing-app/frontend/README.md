# 책 출판 관리 시스템 - 프론트엔드

React 18 + Vite + Material-UI 기반의 책 출판 관리 시스템 프론트엔드 애플리케이션입니다.

## 기술 스택

- **React 18**: UI 라이브러리
- **Vite**: 빌드 도구 및 개발 서버
- **Material-UI (MUI)**: UI 컴포넌트 라이브러리
- **React Router**: 라우팅
- **React Query**: 서버 상태 관리
- **Zustand**: 클라이언트 상태 관리
- **Axios**: HTTP 클라이언트
- **React Hook Form**: 폼 관리
- **React Toastify**: 알림 메시지

## 시작하기

### 사전 준비사항

- Node.js 18 이상
- npm 또는 yarn

### 설치 및 실행

```bash
# 의존성 설치
npm install

# 환경 변수 설정
cp .env.example .env

# 개발 서버 시작
npm run dev
```

개발 서버는 http://localhost:5173 에서 실행됩니다.

### 빌드

```bash
# 프로덕션 빌드
npm run build

# 빌드 결과 미리보기
npm run preview
```

## 프로젝트 구조

```
src/
├── components/         # 재사용 가능한 컴포넌트
│   ├── Layout.jsx     # 메인 레이아웃 (네비게이션, 사이드바)
│   └── PrivateRoute.jsx  # 인증 필요 라우트 보호
├── pages/             # 페이지 컴포넌트
│   ├── Login.jsx      # 로그인 페이지
│   ├── Register.jsx   # 회원가입 페이지
│   ├── Dashboard.jsx  # 대시보드
│   ├── TextbookList.jsx       # 교재 목록
│   ├── TextbookDetail.jsx     # 교재 상세
│   ├── TextbookEditor.jsx     # 교재 편집
│   ├── RegulationList.jsx     # 출판 규정 목록
│   ├── RegulationDetail.jsx   # 출판 규정 상세
│   └── Profile.jsx    # 사용자 프로필
├── services/          # API 서비스
│   └── api.js        # Axios 인스턴스 및 API 함수
├── store/            # 상태 관리
│   └── authStore.js  # 인증 상태 관리 (Zustand)
├── App.jsx           # 메인 앱 컴포넌트
├── main.jsx          # 진입점
└── index.css         # 글로벌 스타일

```

## 주요 기능

### 인증
- 로그인 / 회원가입
- JWT 토큰 기반 인증
- 역할 기반 접근 제어 (ADMIN, EDITOR, REVIEWER, VIEWER)
- 자동 로그인 (토큰 저장)

### 교재 관리
- 교재 목록 조회 및 검색
- 교재 상세 정보 확인
- 교재 생성 및 편집 (편집자 이상)
- 챕터 및 섹션 관리
- 평가 문항 관리

### 출판 규정
- 출판 규정 목록 조회
- 카테고리별 필터링
- 규정 검색
- 규정 상세 정보 확인

### 사용자 관리
- 프로필 조회 및 수정
- 비밀번호 변경

## 환경 변수

`.env` 파일을 생성하고 다음 변수를 설정하세요:

```env
VITE_API_BASE_URL=http://localhost:3000/api
```

## API 연동

백엔드 API와의 통신은 `src/services/api.js`에서 관리합니다.

- 자동 JWT 토큰 첨부
- 오류 처리 및 사용자 알림
- 401 오류 시 자동 로그아웃

## 테스트 계정

백엔드 시드 데이터 실행 시 다음 계정을 사용할 수 있습니다:

- **관리자**: admin@bookpublishing.com / Admin123!
- **편집자**: editor@bookpublishing.com / Editor123!
- **검토자**: reviewer@bookpublishing.com / Reviewer123!

## 개발 가이드

### 새 페이지 추가

1. `src/pages/`에 새 컴포넌트 생성
2. `src/App.jsx`에 라우트 추가
3. 필요시 네비게이션 메뉴에 추가 (`src/components/Layout.jsx`)

### 새 API 추가

1. `src/services/api.js`에 API 함수 추가
2. React Query 훅 사용하여 데이터 가져오기

### 상태 관리

- 서버 상태: React Query 사용
- 클라이언트 상태: Zustand 사용
- 인증 상태는 `useAuthStore` 훅을 통해 접근

## 라이센스

MIT
