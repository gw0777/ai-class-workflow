# 배포 가이드

## 프로덕션 배포 체크리스트

### 1. 사전 준비

- [ ] 토스페이먼츠 사업자 심사 완료
- [ ] 운영용 API 키 발급 완료
- [ ] Firebase 프로젝트 Blaze 플랜 업그레이드
- [ ] 도메인 등록 및 SSL 인증서 설정
- [ ] 환경 변수 운영 환경 값으로 변경

### 2. 토스페이먼츠 운영 설정

```bash
# 1. 토스페이먼츠 개발자센터 접속
# 2. 운영 앱으로 전환
# 3. 운영 API 키 복사

# Firebase Functions 환경 변수 업데이트
firebase functions:config:set toss.secret_key="live_sk_XXXXXXXXXXXXXXXXXXXXXXXX"
```

### 3. 프론트엔드 빌드 및 배포

```bash
cd frontend

# 환경 변수 확인
cat .env

# 프로덕션 빌드
npm run build

# 빌드 결과 확인
ls -la dist/

# Firebase Hosting 배포
firebase deploy --only hosting
```

### 4. Cloud Functions 배포

```bash
cd functions

# TypeScript 컴파일
npm run build

# Functions 배포
firebase deploy --only functions

# 특정 함수만 배포
firebase deploy --only functions:confirmTossPayment
firebase deploy --only functions:handlePaymentWebhook
```

### 5. Firestore 규칙 및 인덱스 배포

```bash
# Firestore 규칙 배포
firebase deploy --only firestore:rules

# Firestore 인덱스 배포
firebase deploy --only firestore:indexes
```

### 6. 도메인 설정

```bash
# Firebase Hosting에 커스텀 도메인 추가
firebase hosting:channel:deploy production

# DNS 설정
# A 레코드 추가: @ -> Firebase IP
# CNAME 레코드: www -> your-project.web.app
```

### 7. 환경 변수 검증

운영 환경 `.env` 파일:

```env
# Toss Payments (운영)
VITE_TOSS_CLIENT_KEY=live_ck_XXXXXXXXXXXXXXXXXXXXXXXX

# Firebase (운영)
VITE_FIREBASE_API_KEY=운영-API-KEY
VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project-id

# App URLs (운영)
VITE_APP_URL=https://yourdomain.com
VITE_API_URL=https://us-central1-your-project-id.cloudfunctions.net

NODE_ENV=production
```

### 8. 토스페이먼츠 웹훅 URL 업데이트

토스페이먼츠 개발자센터에서:

```
웹훅 URL: https://us-central1-[PROJECT_ID].cloudfunctions.net/handlePaymentWebhook
```

### 9. 배포 후 테스트

```bash
# 1. 실제 결제 테스트 (소액)
# 2. 구독 생성 확인
# 3. 결제 이력 확인
# 4. 웹훅 수신 확인
# 5. 이메일 알림 확인

# Functions 로그 모니터링
firebase functions:log --only confirmTossPayment
```

---

## CI/CD 파이프라인 (GitHub Actions)

`.github/workflows/deploy.yml`:

```yaml
name: Deploy to Firebase

on:
  push:
    branches:
      - main

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install Frontend Dependencies
        run: |
          cd frontend
          npm ci

      - name: Build Frontend
        run: |
          cd frontend
          npm run build
        env:
          VITE_TOSS_CLIENT_KEY: ${{ secrets.VITE_TOSS_CLIENT_KEY }}
          VITE_FIREBASE_API_KEY: ${{ secrets.VITE_FIREBASE_API_KEY }}
          VITE_FIREBASE_AUTH_DOMAIN: ${{ secrets.VITE_FIREBASE_AUTH_DOMAIN }}
          VITE_FIREBASE_PROJECT_ID: ${{ secrets.VITE_FIREBASE_PROJECT_ID }}
          VITE_FIREBASE_STORAGE_BUCKET: ${{ secrets.VITE_FIREBASE_STORAGE_BUCKET }}
          VITE_FIREBASE_MESSAGING_SENDER_ID: ${{ secrets.VITE_FIREBASE_MESSAGING_SENDER_ID }}
          VITE_FIREBASE_APP_ID: ${{ secrets.VITE_FIREBASE_APP_ID }}
          VITE_APP_URL: ${{ secrets.VITE_APP_URL }}

      - name: Install Functions Dependencies
        run: |
          cd functions
          npm ci

      - name: Build Functions
        run: |
          cd functions
          npm run build

      - name: Deploy to Firebase
        uses: FirebaseExtended/action-hosting-deploy@v0
        with:
          repoToken: '${{ secrets.GITHUB_TOKEN }}'
          firebaseServiceAccount: '${{ secrets.FIREBASE_SERVICE_ACCOUNT }}'
          projectId: your-project-id
```

---

## 롤백 전략

### 배포 롤백

```bash
# Hosting 이전 버전으로 롤백
firebase hosting:clone SOURCE_SITE_ID:SOURCE_VERSION_ID SITE_ID

# Functions 이전 버전으로 롤백
# Firebase Console → Functions → 함수 선택 → 이전 버전 선택 → 배포
```

### 데이터 롤백

```bash
# Firestore 백업에서 복원
gcloud firestore import gs://[BUCKET_NAME]/[EXPORT_PREFIX]

# 또는 Firebase Console에서 수동 복원
```

---

## 모니터링

### 1. Firebase Performance Monitoring

```typescript
// frontend/src/main.tsx
import { getPerformance } from 'firebase/performance';

const perf = getPerformance(app);
```

### 2. Error Tracking (Sentry)

```bash
npm install @sentry/react @sentry/tracing
```

```typescript
// frontend/src/main.tsx
import * as Sentry from '@sentry/react';

Sentry.init({
  dsn: 'YOUR_SENTRY_DSN',
  environment: 'production',
});
```

### 3. Google Analytics

```typescript
// frontend/src/config/analytics.ts
import { getAnalytics } from 'firebase/analytics';

export const analytics = getAnalytics(app);
```

---

## 보안 체크리스트

- [ ] Firebase Security Rules 검토 완료
- [ ] API 키 환경 변수로 관리
- [ ] HTTPS 강제 적용
- [ ] CORS 설정 확인
- [ ] Rate Limiting 설정
- [ ] DDoS 방어 설정 (Cloud Armor)
- [ ] 개인정보처리방침 게시
- [ ] 이용약관 게시

---

## 성능 최적화

### 1. 프론트엔드

```bash
# 번들 사이즈 분석
npm run build -- --mode production
npx vite-bundle-visualizer

# 이미지 최적화
# - WebP 포맷 사용
# - Lazy Loading 적용
# - CDN 사용
```

### 2. Cloud Functions

```typescript
// 콜드 스타트 최소화
export const confirmTossPayment = functions
  .runWith({
    memory: '512MB',
    timeoutSeconds: 60,
    minInstances: 1, // 최소 인스턴스 유지
  })
  .https.onCall(async (data, context) => {
    // ...
  });
```

### 3. Firestore

- 복합 쿼리에 인덱스 생성
- 문서 크기 1MB 이하 유지
- 컬렉션 그룹 쿼리 최소화

---

## 비용 최적화

### Firebase 요금제

- **Spark (무료)**: 개발/테스트용
- **Blaze (종량제)**: 운영 환경

### 예상 비용 (월 100명 기준)

| 항목 | 예상 비용 |
|------|----------|
| Cloud Functions | $5-10 |
| Firestore | $2-5 |
| Hosting | $0 (무료 한도 내) |
| **합계** | **$7-15** |

---

## 지원 및 문의

- 배포 이슈: GitHub Issues
- 긴급 문의: support@airesume.com
- 문서: https://github.com/your-repo/docs
