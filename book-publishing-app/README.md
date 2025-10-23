# 책 출판을 위한 출판 규정 이해 및 편집자 앱

## 프로젝트 개요

교육 자료를 체계적인 출판용 교재로 개발하고, 편집자가 출판 규정을 관리할 수 있는 통합 시스템

### 주요 기능

1. **출판 규정 관리 시스템**
   - 국내/국제 출판 규정 데이터베이스
   - 규정 검색 및 필터링
   - 버전 관리 및 업데이트 추적

2. **편집자 작업 도구**
   - 원고 편집 및 검토
   - 출판 워크플로우 관리
   - 협업 기능

3. **교재 변환 시스템**
   - PDF/PPTX를 출판용 포맷으로 변환
   - 자동 목차 생성
   - 학습 목표 및 평가 문항 추가

## 기술 스택

### Backend
- **Runtime**: Node.js 18+
- **Framework**: Express.js
- **Database**: PostgreSQL
- **ORM**: Prisma
- **Authentication**: JWT

### Frontend
- **Framework**: React 18+
- **UI Library**: Material-UI
- **State Management**: Redux Toolkit
- **Build Tool**: Vite

### 교재 변환
- **PDF Processing**: pdf-lib, pdf-parse
- **Document Generation**: docx, markdown-it
- **Template Engine**: Handlebars

## 프로젝트 구조

```
book-publishing-app/
├── backend/          # Node.js 백엔드 서버
│   ├── src/
│   │   ├── routes/   # API 라우트
│   │   ├── controllers/  # 비즈니스 로직
│   │   ├── models/   # 데이터 모델
│   │   ├── middleware/  # 미들웨어
│   │   └── utils/    # 유틸리티 함수
│   └── config/       # 설정 파일
│
├── frontend/         # React 프론트엔드
│   ├── src/
│   │   ├── components/  # React 컴포넌트
│   │   ├── pages/    # 페이지 컴포넌트
│   │   ├── services/ # API 서비스
│   │   ├── styles/   # 스타일시트
│   │   └── utils/    # 유틸리티
│   └── public/       # 정적 파일
│
├── database/         # 데이터베이스 스키마 및 마이그레이션
│
└── content/          # 교재 콘텐츠
    ├── textbooks/    # 변환된 교재
    └── source-materials/  # 원본 자료
```

## 설치 및 실행

### 필수 요구사항
- Node.js 18 이상
- PostgreSQL 14 이상
- npm 또는 yarn

### 백엔드 설정

```bash
cd backend
npm install
cp .env.example .env
# .env 파일 설정 후
npm run migrate
npm run dev
```

### 프론트엔드 설정

```bash
cd frontend
npm install
npm run dev
```

## 개발 현황

- [x] 프로젝트 구조 설계
- [ ] 데이터베이스 스키마 설계
- [ ] 백엔드 API 구현
- [ ] 프론트엔드 UI 구현
- [ ] 교재 변환 기능
- [ ] 출판 워크플로우
- [ ] 테스트 및 문서화

## 라이선스

MIT

## 기여자

- Claude Code AI Assistant
