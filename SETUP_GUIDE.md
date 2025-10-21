# 교수-학생 AI 소통 플랫폼 - 설치 가이드

## 빠른 시작 (5분 안에 실행하기)

### 1단계: Anthropic API 키 발급

1. [Anthropic Console](https://console.anthropic.com/)에 접속
2. 계정 생성 또는 로그인
3. API Keys 메뉴에서 새 API 키 생성
4. API 키를 안전한 곳에 복사

### 2단계: Backend 설정

```bash
# 프로젝트 디렉토리로 이동
cd ai-class-workflow/backend

# 의존성 설치
npm install

# 환경 변수 파일 수정
# backend/.env 파일을 열어서 ANTHROPIC_API_KEY를 입력하세요
nano .env  # 또는 선호하는 에디터 사용
```

`.env` 파일 내용:
```
PORT=3000
JWT_SECRET=my-super-secret-jwt-key-change-this-in-production
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx  # 여기에 발급받은 키 입력
NODE_ENV=development
```

### 3단계: Backend 실행

```bash
# backend 디렉토리에서
npm start
```

성공 메시지가 표시되면 Backend가 준비된 것입니다!

### 4단계: Frontend 설정 및 실행

새 터미널 창을 열고:

```bash
cd ai-class-workflow/frontend

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
```

### 5단계: 브라우저에서 접속

브라우저에서 `http://localhost:5173`으로 접속하세요!

## 초기 사용자 생성

### 교수 계정 만들기

1. 회원가입 페이지로 이동
2. 다음 정보 입력:
   - 역할: **교수**
   - 이름: 홍길동
   - 이메일: professor@example.com
   - 비밀번호: password123
   - 학과: 체육교육과
3. "회원가입" 클릭
4. 로그인 페이지에서 로그인

### 학생 계정 만들기

1. 로그아웃 후 회원가입 페이지로 이동
2. 다음 정보 입력:
   - 역할: **학생**
   - 이름: 김철수
   - 이메일: student@example.com
   - 비밀번호: password123
   - 학과: 체육교육과
   - 학번: 20240001
3. "회원가입" 클릭
4. 로그인 페이지에서 로그인

## 기능 테스트

### 교수로 메시지 보내기

1. 교수 계정으로 로그인
2. "메시지 작성" 버튼 클릭
3. 수신자 선택:
   - "개별 학생" 선택
   - 학생 검색 및 선택
4. 메시지 작성:
   ```
   과제를 제출하지 않은 학생들이 있습니다.
   정말 실망스럽네요! 다음부터는 꼭 제출하세요.
   ```
5. "AI 분석 시작" 클릭
6. AI 분석 결과 확인:
   - 감정 분석 결과
   - 위험도 (높음으로 표시될 것)
   - 문제점 목록
   - 개선된 메시지 제안
7. 개선된 메시지 확인 후 "다음 단계"
8. "메시지 전송" 클릭

### 학생으로 메시지 확인하기

1. 로그아웃 후 학생 계정으로 로그인
2. 대시보드에서 읽지 않은 메시지 확인
3. 메시지 목록에서 메시지 클릭
4. 메시지 내용 읽기
5. 피드백 버튼 클릭 (도움됨/명확함/혼란스러움)

## 문제 해결

### "Cannot connect to backend" 에러

**원인**: Backend 서버가 실행되지 않았거나 포트가 다름

**해결**:
```bash
# Backend가 실행 중인지 확인
curl http://localhost:3000/health

# 만약 응답이 없다면 Backend를 시작하세요
cd backend
npm start
```

### "AI analysis failed" 에러

**원인**: Anthropic API 키가 잘못되었거나 만료됨

**해결**:
1. `.env` 파일의 `ANTHROPIC_API_KEY` 확인
2. [Anthropic Console](https://console.anthropic.com/)에서 키 상태 확인
3. 필요시 새 키 발급
4. Backend 재시작

### "Database error" 에러

**원인**: 데이터베이스 파일이 손상되었거나 권한 문제

**해결**:
```bash
# Backend 디렉토리에서
rm database.db  # 기존 데이터베이스 삭제
npm start       # 서버 재시작 (자동으로 새 DB 생성)
```

### Frontend가 로딩되지 않음

**원인**: 의존성이 제대로 설치되지 않음

**해결**:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

## 개발 모드 vs 프로덕션 모드

### 개발 모드 (현재)
- 코드 변경 시 자동 재시작
- 상세한 에러 메시지
- 소스맵 활성화
- 개발 도구 사용 가능

### 프로덕션 모드로 전환

```bash
# Frontend 빌드
cd frontend
npm run build

# 빌드된 파일은 frontend/dist에 생성됨
# 이 파일들을 웹 서버(Nginx, Apache 등)로 서빙

# Backend를 프로덕션 모드로 실행
cd backend
NODE_ENV=production npm start
```

## 추가 설정

### 포트 변경

**Backend 포트 변경**:
```bash
# backend/.env
PORT=4000  # 원하는 포트로 변경
```

**Frontend API URL 변경**:
```bash
# frontend/.env.local 파일 생성
VITE_API_URL=http://localhost:4000/api
```

### JWT 비밀키 변경 (중요!)

프로덕션 환경에서는 반드시 안전한 비밀키를 사용하세요:

```bash
# 랜덤 키 생성
openssl rand -base64 32

# backend/.env에 적용
JWT_SECRET=생성된_랜덤_키
```

## 다음 단계

- 더 많은 학생 계정 만들기
- 그룹 만들기 및 관리
- 다양한 메시지 유형 테스트
- AI 분석 결과 비교

문제가 계속되면 README.md의 문제 해결 섹션을 참조하세요!
