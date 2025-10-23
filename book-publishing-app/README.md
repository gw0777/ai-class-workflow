# 책 출판 관리 시스템

> 교육 자료를 체계적인 출판용 교재로 개발하고, 편집자가 출판 규정을 관리할 수 있는 통합 시스템

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Node.js](https://img.shields.io/badge/Node.js-18+-green.svg)](https://nodejs.org/)
[![React](https://img.shields.io/badge/React-18+-blue.svg)](https://reactjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-12+-blue.svg)](https://www.postgresql.org/)

## 프로젝트 개요

이 시스템은 출판사, 교육 기관, 편집자가 교육 자료를 효율적으로 관리하고 출판할 수 있도록 돕는 종합 플랫폼입니다. 기존 PDF/PPTX 자료를 구조화된 교재로 자동 변환하고, 출판 규정을 체계적으로 관리하며, 협업 편집 워크플로우를 지원합니다.

## 주요 기능

### 1. 교재 관리 시스템
- ✅ 교재 생성, 편집, 조회, 삭제 (CRUD)
- ✅ 챕터 및 섹션 계층 구조
- ✅ 학습 목표 및 요약 관리
- ✅ 평가 문항 통합 관리 (객관식, 주관식, 서술형)
- ✅ 교재 상태 관리 (초안, 검토 중, 승인됨, 출판됨, 보관됨)
- ✅ 메타데이터 관리 (주제, 대상 독자, 난이도, 키워드)

### 2. PDF/PPTX 자동 변환
- ✅ PDF 텍스트 추출 및 구조화
- ✅ 챕터/섹션 자동 인식 (패턴 매칭)
- ✅ 학습 목표 자동 추출
- ✅ PPTX 슬라이드 파싱
- ✅ 소스 자료 관리 및 추적

### 3. 출판 규정 관리
- ✅ 카테고리별 출판 규정 데이터베이스
  - 저작권, ISBN, 편집 형식, 콘텐츠 기준, 유통, 품질, 법적 요건
- ✅ 국가별/버전별 규정 관리
- ✅ 전문 검색 기능 (제목, 내용, 설명)
- ✅ 규정 조회 및 필터링

### 4. 사용자 관리 및 인증
- ✅ JWT 기반 인증
- ✅ 역할 기반 접근 제어 (RBAC)
  - ADMIN: 전체 시스템 관리
  - EDITOR: 교재 편집 및 생성
  - REVIEWER: 교재 검토
  - VIEWER: 열람 전용
- ✅ 사용자 프로필 관리
- ✅ 비밀번호 암호화 (bcrypt)

### 5. 출판 워크플로우 (구조 설계 완료)
- 📋 다단계 승인 프로세스
- 📋 작업 할당 및 추적
- 📋 버전 관리 시스템
- 📋 댓글 및 협업 기능

## 기술 스택

### Backend
- **Runtime**: Node.js 18+
- **Framework**: Express.js 4.18
- **Database**: PostgreSQL 12+
- **ORM**: Prisma 5.7
- **Authentication**: JWT (jsonwebtoken)
- **Security**: Helmet, bcryptjs, CORS
- **Validation**: Joi
- **File Upload**: Multer
- **PDF Processing**: pdf-parse
- **Utilities**: compression, morgan

### Frontend
- **Framework**: React 18.2
- **Build Tool**: Vite 5.0
- **UI Library**: Material-UI (MUI) 5.15
- **Routing**: React Router 6.20
- **State Management**:
  - Zustand (client state)
  - React Query (server state)
- **HTTP Client**: Axios
- **Form Management**: React Hook Form
- **Notifications**: React Toastify
- **Markdown**: React Markdown
- **Date Handling**: date-fns

### Database
- **PostgreSQL** with Prisma ORM
- 15+ models with complex relationships
- Automatic migrations
- Type-safe queries

### Development Tools
- **Nodemon**: Auto-restart for development
- **ESLint**: Code linting
- **Prisma Studio**: Database GUI
- **Git**: Version control

## 프로젝트 구조

```
book-publishing-app/
├── backend/                    # Node.js 백엔드 서버
│   ├── src/
│   │   ├── controllers/        # 비즈니스 로직
│   │   │   ├── textbook.controller.js    # 교재 CRUD
│   │   │   ├── regulation.controller.js  # 출판 규정
│   │   │   ├── user.controller.js        # 사용자 관리
│   │   │   └── converter.controller.js   # 파일 변환
│   │   ├── routes/             # API 라우트
│   │   │   ├── textbook.routes.js
│   │   │   ├── regulation.routes.js
│   │   │   ├── user.routes.js
│   │   │   ├── converter.routes.js
│   │   │   ├── workflow.routes.js
│   │   │   └── upload.routes.js
│   │   ├── middleware/         # 미들웨어
│   │   │   ├── auth.middleware.js        # JWT 인증/인가
│   │   │   └── validation.middleware.js  # Joi 검증
│   │   ├── services/           # 서비스 계층
│   │   │   ├── pdfConverter.js          # PDF 변환
│   │   │   └── pptxConverter.js         # PPTX 변환
│   │   └── server.js           # 메인 서버 파일
│   ├── prisma/
│   │   ├── schema.prisma       # 데이터베이스 스키마
│   │   └── seed.js             # 시드 데이터
│   ├── scripts/
│   │   └── setup.sh            # 자동 설정 스크립트
│   ├── .env.example
│   ├── .gitignore
│   └── package.json
│
├── frontend/                   # React 프론트엔드
│   ├── src/
│   │   ├── components/         # 재사용 컴포넌트
│   │   │   ├── Layout.jsx
│   │   │   └── PrivateRoute.jsx
│   │   ├── pages/              # 페이지 컴포넌트
│   │   │   ├── Login.jsx
│   │   │   ├── Register.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   ├── TextbookList.jsx
│   │   │   ├── TextbookDetail.jsx
│   │   │   ├── TextbookEditor.jsx
│   │   │   ├── RegulationList.jsx
│   │   │   ├── RegulationDetail.jsx
│   │   │   └── Profile.jsx
│   │   ├── services/           # API 서비스
│   │   │   └── api.js          # Axios 인스턴스
│   │   ├── store/              # 상태 관리
│   │   │   └── authStore.js    # Zustand 스토어
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── index.html
│   ├── vite.config.js
│   ├── .env.example
│   ├── .gitignore
│   └── package.json
│
├── database/                   # 데이터베이스 문서
│   ├── schema.prisma           # Prisma 스키마 복사본
│   └── README.md               # 데이터베이스 가이드
│
├── content/                    # 콘텐츠 및 문서
│   └── converter/
│       └── README.md           # 변환 기능 문서
│
├── SETUP_GUIDE.md              # 설치 가이드
└── README.md                   # 프로젝트 소개
```

## 빠른 시작

### 필수 요구사항
- Node.js 18 이상
- PostgreSQL 12 이상
- npm 또는 yarn

### 1분 안에 시작하기

```bash
# 1. 저장소 클론
git clone <repository-url>
cd book-publishing-app

# 2. 데이터베이스 생성
createdb book_publishing_db

# 3. 백엔드 설정 (터미널 1)
cd backend
npm install
cp .env.example .env
# .env 파일에서 DATABASE_URL 설정
npx prisma generate
npx prisma migrate dev --name init
npm run seed
npm run dev

# 4. 프론트엔드 설정 (터미널 2)
cd frontend
npm install
npm run dev
```

### 접속 및 로그인

1. 브라우저에서 http://localhost:5173 접속
2. 시드 데이터로 생성된 계정 사용:
   - **관리자**: admin@bookpublishing.com / Admin123!
   - **편집자**: editor@bookpublishing.com / Editor123!
   - **검토자**: reviewer@bookpublishing.com / Reviewer123!

자세한 설치 가이드는 [SETUP_GUIDE.md](./SETUP_GUIDE.md)를 참조하세요.

## API 문서

### 인증 API

```bash
# 회원가입
POST /api/users/register
Body: { email, password, name, role }

# 로그인
POST /api/users/login
Body: { email, password }

# 프로필 조회
GET /api/users/profile
Headers: Authorization: Bearer <token>
```

### 교재 API

```bash
# 교재 목록
GET /api/textbooks?page=1&limit=10&status=DRAFT&search=keyword

# 교재 상세
GET /api/textbooks/:id

# 교재 생성
POST /api/textbooks
Headers: Authorization: Bearer <token>
Body: { title, author, description, ... }

# 교재 출판
POST /api/textbooks/:id/publish
Headers: Authorization: Bearer <token>
```

### 변환 API

```bash
# 파일 업로드
POST /api/converter/upload
Headers: Authorization: Bearer <token>
Content-Type: multipart/form-data
Body: file=<PDF/PPTX 파일>

# PDF 변환
POST /api/converter/convert/pdf/:sourceId
Headers: Authorization: Bearer <token>
Body: { title, author, subject, ... }
```

전체 API 문서는 서버 실행 후 http://localhost:3000 에서 확인할 수 있습니다.

## 데이터베이스 스키마

주요 테이블:

- **users**: 사용자 정보 및 권한
- **textbooks**: 교재 기본 정보
- **chapters**: 교재 챕터
- **sections**: 챕터 내 섹션
- **assessments**: 평가 문항
- **publishing_regulations**: 출판 규정
- **publishing_workflows**: 출판 워크플로우
- **workflow_steps**: 워크플로우 단계
- **source_materials**: 변환 소스 파일
- **textbook_metadata**: 교재 메타데이터

스키마 상세는 [database/README.md](./database/README.md) 참조

## 개발 현황

- [x] 프로젝트 구조 설계
- [x] 데이터베이스 스키마 설계 (15+ 모델)
- [x] 백엔드 API 구현
  - [x] 사용자 인증 및 관리
  - [x] 교재 CRUD 및 관리
  - [x] 출판 규정 관리
  - [x] PDF/PPTX 변환
- [x] 프론트엔드 UI 구현
  - [x] 인증 페이지 (로그인/회원가입)
  - [x] 대시보드
  - [x] 교재 목록 및 관리
  - [x] 반응형 레이아웃
- [x] 교재 변환 기능
  - [x] PDF 텍스트 추출
  - [x] 구조 인식 및 자동 분류
- [x] 출판 워크플로우 (데이터베이스 스키마)
- [x] 문서화
  - [x] README
  - [x] SETUP_GUIDE
  - [x] API 문서
  - [x] 데이터베이스 가이드
  - [x] 변환 기능 가이드

## 향후 개선 사항

### 단기 목표
- [ ] 교재 상세 페이지 완성
- [ ] 교재 편집기 구현 (WYSIWYG)
- [ ] 출판 규정 상세 페이지
- [ ] 워크플로우 UI 구현
- [ ] 파일 업로드 UI

### 중기 목표
- [ ] 협업 편집 기능 (실시간 동기화)
- [ ] 버전 관리 시스템 UI
- [ ] 댓글 및 리뷰 시스템
- [ ] 알림 시스템
- [ ] 대시보드 통계 차트

### 장기 목표
- [ ] AI 기반 자동 요약
- [ ] OCR 지원 (스캔 PDF)
- [ ] 이미지 및 표 인식
- [ ] 다국어 지원
- [ ] EPUB/PDF 내보내기
- [ ] 모바일 앱

## 기여 방법

이 프로젝트에 기여하고 싶으시다면:

1. 저장소 포크
2. 기능 브랜치 생성 (`git checkout -b feature/amazing-feature`)
3. 변경사항 커밋 (`git commit -m 'Add some amazing feature'`)
4. 브랜치에 푸시 (`git push origin feature/amazing-feature`)
5. Pull Request 생성

### 코드 스타일

- JavaScript: ESLint 규칙 준수
- Git 커밋 메시지: 명확하고 설명적으로 작성
- 코드 리뷰 후 병합

## 문제 해결

일반적인 문제 해결 방법은 [SETUP_GUIDE.md](./SETUP_GUIDE.md#문제-해결) 참조

## 문서

- [설치 가이드](./SETUP_GUIDE.md) - 상세 설치 및 설정 방법
- [백엔드 README](./backend/README.md) - 백엔드 API 문서
- [프론트엔드 README](./frontend/README.md) - 프론트엔드 가이드
- [데이터베이스 가이드](./database/README.md) - 데이터베이스 스키마 및 마이그레이션
- [변환 기능 가이드](./content/converter/README.md) - PDF/PPTX 변환 사용법

## 스크린샷

(향후 추가 예정)

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 감사의 말

이 프로젝트는 다음 오픈소스 프로젝트를 사용합니다:

- [Express.js](https://expressjs.com/) - 백엔드 프레임워크
- [React](https://reactjs.org/) - 프론트엔드 라이브러리
- [Prisma](https://www.prisma.io/) - ORM
- [Material-UI](https://mui.com/) - UI 컴포넌트 라이브러리
- [Vite](https://vitejs.dev/) - 빌드 도구

## 연락처

프로젝트 관련 문의사항이 있으시면 이슈를 생성해주세요.

---

⭐ 이 프로젝트가 도움이 되었다면 별표를 눌러주세요!

🤖 Generated with [Claude Code](https://claude.com/claude-code)
