# 데이터베이스 설정 가이드

## 개요

이 프로젝트는 PostgreSQL 데이터베이스와 Prisma ORM을 사용합니다.

## 사전 준비사항

1. PostgreSQL 설치 (버전 12 이상 권장)
2. Node.js 설치 (버전 18 이상)

## 데이터베이스 설정

### 1. PostgreSQL 데이터베이스 생성

```bash
# PostgreSQL에 접속
psql -U postgres

# 데이터베이스 생성
CREATE DATABASE book_publishing_db;

# 사용자 생성 (선택사항)
CREATE USER book_admin WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE book_publishing_db TO book_admin;
```

### 2. 환경 변수 설정

backend 디렉토리에 `.env` 파일을 생성하고 다음 내용을 입력합니다:

```env
# 서버 설정
NODE_ENV=development
PORT=3000

# 데이터베이스
DATABASE_URL="postgresql://username:password@localhost:5432/book_publishing_db?schema=public"

# JWT 인증
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
JWT_EXPIRES_IN=7d

# 파일 업로드
MAX_FILE_SIZE=52428800

# CORS
CORS_ORIGIN=http://localhost:5173
```

### 3. Prisma 마이그레이션 실행

```bash
# backend 디렉토리로 이동
cd backend

# 의존성 설치
npm install

# Prisma 클라이언트 생성
npx prisma generate

# 마이그레이션 실행
npx prisma migrate dev --name init

# (선택) Prisma Studio로 데이터 확인
npx prisma studio
```

### 4. 초기 데이터 시드 (선택사항)

초기 관리자 계정 및 샘플 데이터를 생성하려면:

```bash
npm run seed
```

## 데이터베이스 스키마 구조

### 주요 모델

1. **User**: 사용자 관리
   - 역할: ADMIN, EDITOR, REVIEWER, VIEWER

2. **Textbook**: 교재 관리
   - 상태: DRAFT, IN_REVIEW, APPROVED, PUBLISHED, ARCHIVED

3. **Chapter**: 챕터 관리
   - 교재의 각 장

4. **Section**: 섹션 관리
   - 챕터 내 하위 섹션

5. **Assessment**: 평가 문항
   - 문제 유형: MULTIPLE_CHOICE, TRUE_FALSE, SHORT_ANSWER, ESSAY

6. **PublishingRegulation**: 출판 규정
   - 카테고리별 출판 규정 관리

7. **PublishingWorkflow**: 출판 워크플로우
   - 교재 출판 프로세스 관리

8. **WorkflowStep**: 워크플로우 단계
   - 각 워크플로우의 세부 단계

## 유용한 Prisma 명령어

```bash
# Prisma Studio 실행 (GUI 데이터 관리 도구)
npx prisma studio

# 스키마 변경 후 마이그레이션 생성
npx prisma migrate dev --name migration_name

# 프로덕션 마이그레이션 배포
npx prisma migrate deploy

# 데이터베이스 초기화 (주의: 모든 데이터 삭제)
npx prisma migrate reset

# Prisma 클라이언트 재생성
npx prisma generate

# 데이터베이스 상태 확인
npx prisma migrate status
```

## 트러블슈팅

### 연결 오류

데이터베이스 연결 오류가 발생하는 경우:

1. PostgreSQL 서비스가 실행 중인지 확인
2. `.env` 파일의 `DATABASE_URL`이 올바른지 확인
3. 데이터베이스가 생성되었는지 확인
4. 방화벽 설정 확인

### 마이그레이션 오류

마이그레이션 오류가 발생하는 경우:

```bash
# 마이그레이션 상태 확인
npx prisma migrate status

# 문제가 있는 경우 초기화 (개발 환경에서만)
npx prisma migrate reset
```

## 백업 및 복원

### 백업

```bash
pg_dump -U username -d book_publishing_db > backup.sql
```

### 복원

```bash
psql -U username -d book_publishing_db < backup.sql
```

## 프로덕션 배포 시 주의사항

1. 강력한 데이터베이스 비밀번호 사용
2. SSL 연결 활성화
3. 정기적인 백업 설정
4. 연결 풀 설정 최적화
5. JWT_SECRET 값 변경
6. 환경 변수 보안 관리
