# AI Resume Master - 토스 결제 통합 설정 가이드

## 목차
1. [사전 준비사항](#사전-준비사항)
2. [토스페이먼츠 설정](#토스페이먼츠-설정)
3. [Firebase 프로젝트 설정](#firebase-프로젝트-설정)
4. [로컬 개발 환경 구성](#로컬-개발-환경-구성)
5. [배포](#배포)
6. [테스트](#테스트)

---

## 사전 준비사항

### 필수 도구 설치

```bash
# Node.js 18 이상
node --version  # v18.0.0 이상

# Firebase CLI
npm install -g firebase-tools

# Git
git --version
```

### 필요한 계정

1. **토스페이먼츠 계정**
   - https://www.tosspayments.com 가입
   - 사업자등록증 준비
   - 심사 완료 필요 (2-3 영업일)

2. **Firebase 프로젝트**
   - https://console.firebase.google.com 접속
   - 새 프로젝트 생성

---

## 토스페이먼츠 설정

### 1. 토스페이먼츠 가입 및 인증

1. [토스페이먼츠 개발자센터](https://developers.tosspayments.com) 접속
2. 회원가입 후 로그인
3. **내 앱 관리** → **앱 등록**
4. 사업자 정보 입력 및 서류 제출

### 2. API 키 발급

**개발용 키 (테스트)**
```
Client Key: test_ck_XXXXXXXXXXXXXXXXXXXXXXXX
Secret Key: test_sk_XXXXXXXXXXXXXXXXXXXXXXXX
```

**운영용 키 (심사 승인 후)**
```
Client Key: live_ck_XXXXXXXXXXXXXXXXXXXXXXXX
Secret Key: live_sk_XXXXXXXXXXXXXXXXXXXXXXXX
```

### 3. 결제 설정

1. **결제 수단 선택**
   - 카드 결제 활성화
   - 계좌이체 활성화
   - 정기결제(자동결제) 활성화

2. **웹훅 URL 설정**
   ```
   개발: http://localhost:5001/[PROJECT_ID]/us-central1/handlePaymentWebhook
   운영: https://us-central1-[PROJECT_ID].cloudfunctions.net/handlePaymentWebhook
   ```

3. **리다이렉트 URL 등록**
   ```
   성공: https://yourdomain.com/payment/success
   실패: https://yourdomain.com/payment/fail
   ```

---

## Firebase 프로젝트 설정

### 1. Firebase 프로젝트 생성

```bash
# Firebase 로그인
firebase login

# 프로젝트 초기화
firebase init

# 선택 항목:
# - Firestore
# - Functions
# - Hosting
```

### 2. Firebase 프로젝트 ID 설정

`.firebaserc` 파일 수정:

```json
{
  "projects": {
    "default": "your-project-id"
  }
}
```

### 3. Firebase Functions 환경 변수 설정

```bash
# 토스 Secret Key 설정
firebase functions:config:set toss.secret_key="YOUR_TOSS_SECRET_KEY"

# 확인
firebase functions:config:get
```

### 4. Firestore 규칙 및 인덱스 배포

```bash
# Firestore 규칙 배포
firebase deploy --only firestore:rules

# Firestore 인덱스 배포
firebase deploy --only firestore:indexes
```

### 5. Firebase Authentication 설정

1. Firebase Console → **Authentication** 메뉴
2. **Sign-in method** 탭
3. 활성화할 인증 방법 선택:
   - 이메일/비밀번호
   - Google
   - 카카오 (선택사항)

---

## 로컬 개발 환경 구성

### 1. 프로젝트 클론 및 의존성 설치

```bash
# 프로젝트 클론
git clone [YOUR_REPO_URL]
cd ai-resume-master

# 프론트엔드 의존성 설치
cd frontend
npm install

# Cloud Functions 의존성 설치
cd ../functions
npm install
```

### 2. 환경 변수 설정

루트 디렉토리에 `.env` 파일 생성:

```bash
cp .env.example .env
```

`.env` 파일 수정:

```env
# Toss Payments
VITE_TOSS_CLIENT_KEY=test_ck_XXXXXXXXXXXXXXXXXXXXXXXX
TOSS_SECRET_KEY=test_sk_XXXXXXXXXXXXXXXXXXXXXXXX

# Firebase
VITE_FIREBASE_API_KEY=your-api-key
VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project-id
VITE_FIREBASE_STORAGE_BUCKET=your-project.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=your-sender-id
VITE_FIREBASE_APP_ID=your-app-id

# App
VITE_APP_URL=http://localhost:5173
VITE_API_URL=http://localhost:5001
NODE_ENV=development
```

### 3. Firebase 에뮬레이터 실행

```bash
# 루트 디렉토리에서
firebase emulators:start

# 에뮬레이터 UI 접속
# http://localhost:4000
```

### 4. 프론트엔드 개발 서버 실행

```bash
cd frontend
npm run dev

# 브라우저에서 접속
# http://localhost:5173
```

---

## 배포

### 1. 프론트엔드 빌드

```bash
cd frontend
npm run build
```

### 2. Firebase 전체 배포

```bash
# 루트 디렉토리에서
firebase deploy

# 또는 개별 배포
firebase deploy --only functions    # Functions만
firebase deploy --only hosting      # Hosting만
firebase deploy --only firestore    # Firestore만
```

### 3. 운영 환경 환경 변수 업데이트

```bash
# 운영용 토스 Secret Key 설정
firebase functions:config:set toss.secret_key="live_sk_XXXXXXXXXXXXXXXXXXXXXXXX"

# 재배포
firebase deploy --only functions
```

### 4. 배포 확인

- **Hosting URL**: https://your-project-id.web.app
- **Functions URL**: https://us-central1-your-project-id.cloudfunctions.net

---

## 테스트

### 1. 테스트 카드 정보 (토스페이먼츠)

```
카드번호: 4330-1234-5678-9012
유효기간: 12/25
CVC: 123
비밀번호 앞 2자리: 00
```

### 2. 결제 플로우 테스트

1. **구독 플랜 선택**
   - http://localhost:5173/pricing
   - 플랜 선택 → 결제하기 버튼 클릭

2. **결제 진행**
   - 토스 결제창 팝업 확인
   - 테스트 카드 정보 입력
   - 결제 완료

3. **결제 성공 확인**
   - `/payment/success` 페이지로 리다이렉트
   - Firestore에 구독 정보 저장 확인
   - 대시보드에서 구독 상태 확인

4. **결제 실패 테스트**
   - 잘못된 카드 정보 입력
   - `/payment/fail` 페이지로 리다이렉트 확인

### 3. Cloud Functions 테스트

```bash
# 로컬 에뮬레이터에서 테스트
firebase emulators:start

# Functions 로그 확인
firebase functions:log
```

### 4. 구독 관리 테스트

1. **구독 조회**
   - 대시보드에서 현재 구독 정보 확인

2. **구독 취소**
   - 구독 취소 버튼 클릭
   - 상태가 'cancelled'로 변경 확인

3. **만료 확인 스케줄러**
   ```bash
   # Cloud Scheduler 수동 실행 (Firebase Console)
   # 또는 로컬에서 함수 직접 호출
   ```

---

## 문제 해결

### 결제 오류

**증상**: 결제 요청 시 오류 발생

**해결책**:
1. 토스 API 키 확인
2. CORS 설정 확인
3. Firebase Functions 로그 확인

### 구독 정보 조회 실패

**증상**: Firestore에서 구독 정보를 가져오지 못함

**해결책**:
1. Firestore 보안 규칙 확인
2. 사용자 인증 상태 확인
3. 인덱스 생성 확인

### 웹훅 미수신

**증상**: 토스에서 웹훅이 전달되지 않음

**해결책**:
1. 웹훅 URL 확인
2. HTTPS 설정 확인 (운영 환경)
3. 토스 개발자센터에서 웹훅 로그 확인

---

## 지원

- **이메일**: support@airesume.com
- **문서**: https://github.com/your-repo/docs
- **이슈 리포트**: https://github.com/your-repo/issues

---

## 라이선스

MIT License
