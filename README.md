# AI Resume Master - 토스 결제 통합

AI 기반 이력서 분석 및 최적화 서비스에 토스페이먼츠 구독 결제 시스템을 통합한 프로젝트입니다.

## 주요 기능

### 결제 시스템
- ✅ 토스페이먼츠 PG 연동
- ✅ 카드 결제 및 계좌이체 지원
- ✅ 정기 구독 결제 (자동 갱신)
- ✅ 일회성 결제 옵션
- ✅ 결제 내역 관리
- ✅ 환불 처리 시스템

### 구독 플랜

| 플랜 | 가격 | 주요 기능 |
|------|------|----------|
| **Free** | 무료 | 월 3회 ATS 분석, 기본 템플릿 1종 |
| **Starter** | ₩9,900/월 | 무제한 ATS 분석, 프리미엄 템플릿 5종, 키워드 최적화 |
| **Pro** | ₩29,900/월 | 전체 기능, AI 사진분석, 음성 인터뷰, 1:1 컨설팅 |

### 기술 스택

**Frontend**
- React 18 + TypeScript
- Vite
- Zustand (상태 관리)
- Toss Payments SDK
- Firebase SDK

**Backend**
- Firebase Cloud Functions
- Firestore (NoSQL Database)
- Firebase Authentication
- Cloud Scheduler (구독 만료 관리)

**Payment**
- 토스페이먼츠 (PG)
- 수수료: 2.9%
- 정산: D+2 영업일

## 프로젝트 구조

```
ai-resume-master/
├── frontend/                 # React 프론트엔드
│   ├── src/
│   │   ├── components/       # UI 컴포넌트
│   │   │   ├── payment/      # 결제 관련 컴포넌트
│   │   │   └── subscription/ # 구독 관리 컴포넌트
│   │   ├── services/         # 서비스 레이어
│   │   │   ├── tossPaymentService.ts
│   │   │   ├── subscriptionService.ts
│   │   │   └── firebaseService.ts
│   │   └── config/           # 설정 파일
│   │       ├── tossConfig.ts
│   │       └── subscriptionPlans.ts
│   └── package.json
│
├── functions/                # Cloud Functions
│   ├── src/
│   │   ├── payment/          # 결제 관련 함수
│   │   │   ├── confirmPayment.ts
│   │   │   ├── webhook.ts
│   │   │   └── refund.ts
│   │   └── subscription/     # 구독 관리 함수
│   │       ├── checkExpired.ts
│   │       └── renew.ts
│   └── package.json
│
├── firestore/                # Firestore 설정
│   ├── rules/                # 보안 규칙
│   └── indexes/              # 인덱스 설정
│
├── docs/                     # 문서
│   ├── SETUP_GUIDE.md        # 설정 가이드
│   └── DEPLOYMENT.md         # 배포 가이드
│
├── firebase.json             # Firebase 설정
├── .firebaserc              # Firebase 프로젝트 설정
└── .env.example             # 환경 변수 템플릿
```

## 빠른 시작

### 1. 사전 준비

```bash
# Node.js 18 이상 필요
node --version

# Firebase CLI 설치
npm install -g firebase-tools
```

### 2. 프로젝트 설정

```bash
# 저장소 클론
git clone [YOUR_REPO_URL]
cd ai-resume-master

# 의존성 설치
cd frontend && npm install
cd ../functions && npm install

# 환경 변수 설정
cp .env.example .env
# .env 파일 수정 (토스 API 키, Firebase 설정)
```

### 3. 개발 서버 실행

```bash
# 터미널 1: Firebase 에뮬레이터
firebase emulators:start

# 터미널 2: 프론트엔드 개발 서버
cd frontend
npm run dev

# 브라우저에서 접속
# http://localhost:5173
```

## 주요 컴포넌트

### 결제 플로우

```typescript
// 1. 플랜 선택
<PricingCard
  plan={plan}
  onSelectPlan={handleSelectPlan}
/>

// 2. 결제 모달
<PaymentModal
  isOpen={true}
  planId="starter"
  userId={userId}
  userName={userName}
  userEmail={userEmail}
  onClose={handleClose}
/>

// 3. 결제 성공/실패 처리
<PaymentSuccess />
<PaymentFail />
```

### 구독 관리

```typescript
// 구독 상태 확인
<SubscriptionStatus userId={userId} />

// 구독 취소
await subscriptionService.cancelSubscription(userId);

// 구독 갱신
await subscriptionService.renewSubscription(userId);
```

## API 엔드포인트

### Cloud Functions

| 함수 | 용도 | 메서드 |
|------|------|--------|
| `confirmTossPayment` | 결제 승인 | HTTPS Callable |
| `handlePaymentWebhook` | 웹훅 처리 | HTTPS Request |
| `refundPayment` | 환불 처리 | HTTPS Callable |
| `renewSubscription` | 구독 갱신 | HTTPS Callable |
| `checkExpiredSubscriptions` | 만료 확인 (스케줄러) | Pub/Sub |

## 데이터베이스 스키마

### Firestore Collections

**subscriptions**
```typescript
{
  userId: string;
  planId: 'free' | 'starter' | 'pro';
  status: 'active' | 'cancelled' | 'expired' | 'pending';
  startDate: Timestamp;
  endDate: Timestamp;
  paymentKey?: string;
  orderId?: string;
  amount: number;
  autoRenew: boolean;
  cancelledAt?: Timestamp;
  createdAt: Timestamp;
  updatedAt: Timestamp;
}
```

**paymentHistory**
```typescript
{
  userId: string;
  orderId: string;
  paymentKey: string;
  amount: number;
  planId: string;
  status: 'completed' | 'failed' | 'cancelled' | 'refunded';
  paymentMethod: string;
  paidAt: Timestamp;
  refundedAt?: Timestamp;
  metadata?: any;
}
```

## 테스트

### 테스트 카드 정보

```
카드번호: 4330-1234-5678-9012
유효기간: 12/25
CVC: 123
비밀번호: 00
```

### 로컬 테스트

```bash
# 에뮬레이터 실행
firebase emulators:start

# 결제 테스트
# 1. http://localhost:5173/pricing 접속
# 2. 플랜 선택
# 3. 테스트 카드로 결제
# 4. 성공/실패 확인
```

## 배포

### 프로덕션 배포

```bash
# 1. 프론트엔드 빌드
cd frontend
npm run build

# 2. Firebase 배포
firebase deploy

# 또는 개별 배포
firebase deploy --only functions
firebase deploy --only hosting
firebase deploy --only firestore
```

자세한 배포 가이드는 [DEPLOYMENT.md](docs/DEPLOYMENT.md)를 참고하세요.

## 보안

- ✅ PCI DSS 준수 (토스페이먼츠 제공)
- ✅ HTTPS 강제 적용
- ✅ Firestore Security Rules
- ✅ Firebase Authentication
- ✅ 환경 변수로 민감 정보 관리
- ✅ CORS 설정

## 모니터링

```bash
# Functions 로그
firebase functions:log

# 특정 함수 로그
firebase functions:log --only confirmTossPayment

# 실시간 로그
firebase functions:log --follow
```

## 비용 구조

### 토스페이먼츠 수수료
- 카드 결제: 2.9%
- 계좌이체: 무료 (개인 계좌)
- 정산 주기: D+2 영업일

### Firebase 비용 (예상)
- Cloud Functions: $5-10/월
- Firestore: $2-5/월
- Hosting: 무료 (무료 한도 내)

**총 예상 비용**: $7-15/월 (월 100명 기준)

## 수익 시뮬레이션

```
월별 예상 (런칭 6개월 후):
- 무료 사용자: 1,000명
- Starter 구독: 100명 × ₩9,900 = ₩990,000
- Pro 구독: 20명 × ₩29,900 = ₩598,000
- 월 매출: ₩1,588,000
- 수수료 차감 후: ₩1,541,948
```

## 문서

- [설정 가이드](docs/SETUP_GUIDE.md) - 상세 설정 방법
- [배포 가이드](docs/DEPLOYMENT.md) - 프로덕션 배포

## 지원

- **이메일**: support@airesume.com
- **이슈**: [GitHub Issues](https://github.com/your-repo/issues)
- **문서**: [Wiki](https://github.com/your-repo/wiki)

## 라이선스

MIT License

---

## 즉시 실행 체크리스트

### Week 1
- [ ] 토스페이먼츠 가입
- [ ] 테스트 API 키 발급
- [ ] Firebase 프로젝트 생성
- [ ] 로컬 개발 환경 구성
- [ ] 결제 플로우 테스트

### Week 2
- [ ] Cloud Functions 배포
- [ ] Firestore 규칙 설정
- [ ] 웹훅 테스트
- [ ] 구독 관리 기능 테스트
- [ ] 프로덕션 배포 준비

---

**토스 결제 통합으로 한국 사용자에게 최적화된 결제 경험을 제공하세요!** 🚀
