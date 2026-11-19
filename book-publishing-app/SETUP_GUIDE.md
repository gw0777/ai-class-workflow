# 책 출판 관리 시스템 - 설치 가이드

이 문서는 책 출판 관리 시스템을 처음부터 설치하고 실행하는 방법을 단계별로 안내합니다.

## 목차

1. [사전 준비사항](#사전-준비사항)
2. [데이터베이스 설정](#데이터베이스-설정)
3. [백엔드 설정](#백엔드-설정)
4. [프론트엔드 설정](#프론트엔드-설정)
5. [전체 시스템 실행](#전체-시스템-실행)
6. [문제 해결](#문제-해결)

## 사전 준비사항

### 필수 소프트웨어

1. **Node.js** (버전 18 이상)
   ```bash
   # 버전 확인
   node --version
   npm --version
   ```
   - 설치: https://nodejs.org/

2. **PostgreSQL** (버전 12 이상)
   ```bash
   # 버전 확인
   psql --version
   ```
   - 설치: https://www.postgresql.org/download/

3. **Git**
   ```bash
   # 버전 확인
   git --version
   ```

### 선택 소프트웨어

- **Postman** 또는 **Insomnia**: API 테스트용
- **pgAdmin**: PostgreSQL GUI 관리 도구

## 데이터베이스 설정

### 1. PostgreSQL 데이터베이스 생성

```bash
# PostgreSQL에 접속
psql -U postgres

# 데이터베이스 생성
CREATE DATABASE book_publishing_db;

# (선택사항) 전용 사용자 생성
CREATE USER book_admin WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE book_publishing_db TO book_admin;

# 종료
\q
```

### 2. 데이터베이스 연결 확인

```bash
psql -U postgres -d book_publishing_db -c "SELECT version();"
```

## 백엔드 설정

### 1. 디렉토리 이동

```bash
cd book-publishing-app/backend
```

### 2. 환경 변수 설정

```bash
# .env 파일 생성
cp .env.example .env
```

`.env` 파일을 편집하여 다음 값을 설정하세요:

```env
# 서버 설정
NODE_ENV=development
PORT=3000

# 데이터베이스 (실제 정보로 변경)
DATABASE_URL="postgresql://postgres:your_password@localhost:5432/book_publishing_db?schema=public"

# JWT 인증 (프로덕션에서는 반드시 변경)
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
JWT_EXPIRES_IN=7d

# 파일 업로드
MAX_FILE_SIZE=52428800

# CORS
CORS_ORIGIN=http://localhost:5173
```

### 3. 의존성 설치

```bash
npm install
```

### 4. Prisma 설정 및 마이그레이션

```bash
# Prisma 클라이언트 생성
npx prisma generate

# 데이터베이스 마이그레이션 실행
npx prisma migrate dev --name init
```

### 5. 시드 데이터 생성 (선택사항)

샘플 데이터와 테스트 계정을 생성합니다:

```bash
npm run seed
```

생성되는 테스트 계정:
- **관리자**: admin@bookpublishing.com / Admin123!
- **편집자**: editor@bookpublishing.com / Editor123!
- **검토자**: reviewer@bookpublishing.com / Reviewer123!

### 6. 백엔드 서버 실행

```bash
# 개발 모드로 실행
npm run dev

# 또는 일반 모드
npm start
```

서버가 http://localhost:3000 에서 실행됩니다.

### 7. 백엔드 동작 확인

브라우저나 curl로 확인:

```bash
curl http://localhost:3000/health
```

응답:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00.000Z",
  "uptime": 1.234
}
```

## 프론트엔드 설정

### 1. 새 터미널 열기

백엔드 서버는 실행 중인 상태로 두고, 새 터미널을 엽니다.

### 2. 디렉토리 이동

```bash
cd book-publishing-app/frontend
```

### 3. 환경 변수 설정

```bash
# .env 파일 생성
cp .env.example .env
```

`.env` 파일 내용 확인:

```env
VITE_API_BASE_URL=http://localhost:3000/api
```

### 4. 의존성 설치

```bash
npm install
```

### 5. 프론트엔드 서버 실행

```bash
npm run dev
```

서버가 http://localhost:5173 에서 실행됩니다.

### 6. 브라우저에서 확인

브라우저를 열고 http://localhost:5173 으로 접속합니다.

## 전체 시스템 실행

### 개발 환경

두 개의 터미널을 사용합니다:

**터미널 1 - 백엔드:**
```bash
cd book-publishing-app/backend
npm run dev
```

**터미널 2 - 프론트엔드:**
```bash
cd book-publishing-app/frontend
npm run dev
```

### 스크립트 자동화 (선택사항)

다음 스크립트를 프로젝트 루트에 `start-dev.sh`로 저장:

```bash
#!/bin/bash

# 백엔드 시작
cd backend
npm run dev &
BACKEND_PID=$!

# 프론트엔드 시작
cd ../frontend
npm run dev &
FRONTEND_PID=$!

# 종료 시그널 처리
trap "kill $BACKEND_PID $FRONTEND_PID" EXIT

# 대기
wait
```

실행:
```bash
chmod +x start-dev.sh
./start-dev.sh
```

## 시스템 사용하기

### 1. 로그인

1. 브라우저에서 http://localhost:5173 접속
2. 시드 데이터를 생성했다면 테스트 계정으로 로그인:
   - 이메일: `admin@bookpublishing.com`
   - 비밀번호: `Admin123!`

### 2. 주요 기능 둘러보기

- **대시보드**: 시스템 통계 확인
- **교재 관리**: 교재 생성, 편집, 조회
- **출판 규정**: 출판 규정 검색 및 조회
- **프로필**: 사용자 정보 관리

### 3. 교재 생성

1. 좌측 메뉴에서 "교재 관리" 클릭
2. "새 교재 생성" 버튼 클릭
3. 교재 정보 입력 후 저장

### 4. PDF/PPTX 변환

API를 통해 기존 교육 자료를 변환할 수 있습니다:

```bash
# 1. 파일 업로드
curl -X POST http://localhost:3000/api/converter/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/your/file.pdf"

# 2. 변환 실행
curl -X POST http://localhost:3000/api/converter/convert/pdf/SOURCE_ID \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "교재 제목",
    "author": "저자명",
    "subject": "과목",
    "targetAudience": "대상 독자",
    "difficulty": "intermediate"
  }'
```

## 문제 해결

### 데이터베이스 연결 오류

**증상:**
```
Error: P1001: Can't reach database server
```

**해결 방법:**
1. PostgreSQL 서비스가 실행 중인지 확인
   ```bash
   # Linux/Mac
   sudo systemctl status postgresql

   # Windows
   # 서비스 관리자에서 PostgreSQL 확인
   ```
2. `.env`의 `DATABASE_URL`이 올바른지 확인
3. 데이터베이스가 생성되었는지 확인

### 포트 충돌

**증상:**
```
Error: listen EADDRINUSE: address already in use :::3000
```

**해결 방법:**
1. 다른 프로세스가 포트를 사용 중인지 확인
   ```bash
   # Linux/Mac
   lsof -i :3000

   # Windows
   netstat -ano | findstr :3000
   ```
2. 해당 프로세스 종료 또는 다른 포트 사용
   - `.env`에서 `PORT` 값 변경

### Prisma 마이그레이션 오류

**증상:**
```
Error: Migration failed
```

**해결 방법:**
1. 데이터베이스 초기화 (개발 환경에서만)
   ```bash
   npx prisma migrate reset
   ```
2. 마이그레이션 재실행
   ```bash
   npx prisma migrate dev --name init
   ```

### 프론트엔드 빌드 오류

**증상:**
```
Error: Cannot find module ...
```

**해결 방법:**
1. node_modules 삭제 후 재설치
   ```bash
   rm -rf node_modules package-lock.json
   npm install
   ```

### CORS 오류

**증상:**
```
Access to fetch at 'http://localhost:3000/api/...' from origin 'http://localhost:5173' has been blocked by CORS policy
```

**해결 방법:**
1. 백엔드 `.env`의 `CORS_ORIGIN`이 프론트엔드 URL과 일치하는지 확인
2. 백엔드 서버 재시작

## 프로덕션 배포

### 백엔드 배포

1. 환경 변수 설정
   ```env
   NODE_ENV=production
   DATABASE_URL=your_production_database_url
   JWT_SECRET=strong_random_secret
   ```

2. 빌드 및 실행
   ```bash
   npm run migrate:deploy
   npm start
   ```

### 프론트엔드 배포

1. 빌드
   ```bash
   npm run build
   ```

2. 생성된 `dist` 폴더를 웹 서버에 배포
   - Nginx, Apache, Vercel, Netlify 등 사용 가능

## 추가 도구

### Prisma Studio

데이터베이스 GUI 관리:

```bash
cd backend
npm run studio
```

http://localhost:5555 에서 접속

### API 문서

백엔드 API 엔드포인트 목록:

```bash
curl http://localhost:3000/
```

## 도움말

- [백엔드 README](backend/README.md)
- [프론트엔드 README](frontend/README.md)
- [데이터베이스 가이드](database/README.md)
- [변환 기능 가이드](content/converter/README.md)

## 지원

문제가 발생하면 다음을 확인하세요:
1. 모든 사전 준비사항이 설치되었는지
2. 환경 변수가 올바르게 설정되었는지
3. 데이터베이스가 실행 중이고 접근 가능한지
4. 포트가 충돌하지 않는지
