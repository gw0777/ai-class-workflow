# API Reference

## Cloud Functions API

### 결제 관련 Functions

#### `confirmTossPayment`

토스페이먼츠 결제를 승인하고 구독을 생성합니다.

**타입**: HTTPS Callable
**인증**: Required

**Request**
```typescript
{
  paymentKey: string;    // 토스 결제 키
  orderId: string;       // 주문 ID
  amount: number;        // 결제 금액
  userId: string;        // 사용자 ID
  planId: string;        // 플랜 ID ('free' | 'starter' | 'pro')
}
```

**Response**
```typescript
{
  success: boolean;
  subscription?: {
    userId: string;
    planId: string;
    status: string;
    startDate: Timestamp;
    endDate: Timestamp;
    amount: number;
    // ...
  };
  error?: string;
}
```

**사용 예시**
```typescript
import { getFunctions, httpsCallable } from 'firebase/functions';

const functions = getFunctions();
const confirmPayment = httpsCallable(functions, 'confirmTossPayment');

const result = await confirmPayment({
  paymentKey: 'payment_key_here',
  orderId: 'ORDER_123',
  amount: 9900,
  userId: 'user123',
  planId: 'starter'
});
```

---

#### `handlePaymentWebhook`

토스페이먼츠 웹훅을 처리합니다.

**타입**: HTTPS Request
**인증**: Not Required (토스에서 호출)

**Request (POST)**
```typescript
{
  eventType: string;
  data: {
    paymentKey: string;
    orderId: string;
    status: string;
    amount: number;
    // ...
  };
  createdAt: string;
}
```

**이벤트 타입**
- `PAYMENT_STATUS_CHANGED`: 결제 상태 변경
- `PAYMENT_CANCELED`: 결제 취소
- `PAYMENT_REFUNDED`: 환불 완료
- `SUBSCRIPTION_RENEWED`: 구독 갱신

**Response**
```typescript
{
  success: boolean;
  error?: string;
}
```

---

#### `refundPayment`

결제를 환불 처리합니다.

**타입**: HTTPS Callable
**인증**: Required (관리자만)

**Request**
```typescript
{
  paymentKey: string;      // 결제 키
  cancelReason: string;    // 환불 사유
  refundAmount?: number;   // 부분 환불 금액 (선택)
}
```

**Response**
```typescript
{
  success: boolean;
  refundId?: string;
  error?: string;
}
```

**사용 예시**
```typescript
const refund = httpsCallable(functions, 'refundPayment');

await refund({
  paymentKey: 'payment_key',
  cancelReason: '고객 요청',
  refundAmount: 9900  // 전액 환불
});
```

---

### 구독 관련 Functions

#### `renewSubscription`

구독을 수동으로 갱신합니다.

**타입**: HTTPS Callable
**인증**: Required

**Request**
```typescript
{
  userId: string;
}
```

**Response**
```typescript
{
  success: boolean;
  subscription?: {
    // 갱신된 구독 정보
  };
  error?: string;
}
```

**사용 예시**
```typescript
const renew = httpsCallable(functions, 'renewSubscription');

await renew({
  userId: 'user123'
});
```

---

#### `checkExpiredSubscriptions`

만료된 구독을 확인하고 처리합니다. (자동 실행)

**타입**: Pub/Sub (Cloud Scheduler)
**스케줄**: 매일 자정 (Asia/Seoul)

**로직**
1. 만료된 구독 조회
2. 상태를 'expired'로 업데이트
3. 만료 알림 이메일 발송

---

## Frontend Services API

### TossPaymentService

```typescript
class TossPaymentService {
  // SDK 초기화
  async initialize(): Promise<void>

  // 구독 결제 요청
  async requestSubscriptionPayment(request: PaymentRequest): Promise<void>

  // 일회성 결제 요청
  async requestOneTimePayment(request: PaymentRequest): Promise<void>

  // 계좌이체 결제 요청
  async requestTransferPayment(request: PaymentRequest): Promise<void>

  // URL에서 결제 정보 추출
  getPaymentInfoFromUrl(): {
    paymentKey: string | null;
    orderId: string | null;
    amount: string | null;
  }

  // 결제 실패 정보 추출
  getPaymentFailInfo(): {
    code: string | null;
    message: string | null;
  }
}
```

**사용 예시**
```typescript
import { tossPaymentService } from './services/tossPaymentService';

// 결제 요청
await tossPaymentService.requestSubscriptionPayment({
  planId: 'starter',
  userId: 'user123',
  userName: '홍길동',
  userEmail: 'user@example.com'
});
```

---

### SubscriptionService

```typescript
class SubscriptionService {
  // 구독 정보 조회
  async getUserSubscription(userId: string): Promise<Subscription | null>

  // 구독 생성
  async createSubscription(subscription: Omit<Subscription, 'createdAt' | 'updatedAt'>): Promise<void>

  // 구독 업데이트
  async updateSubscription(userId: string, updates: Partial<Subscription>): Promise<void>

  // 구독 취소
  async cancelSubscription(userId: string): Promise<void>

  // 결제 이력 저장
  async savePaymentHistory(payment: Omit<PaymentHistory, 'id'>): Promise<void>

  // 결제 이력 조회
  async getUserPaymentHistory(userId: string): Promise<PaymentHistory[]>

  // 구독 활성화 여부
  async isSubscriptionActive(userId: string): Promise<boolean>

  // 만료까지 남은 일수
  getDaysUntilExpiration(subscription: Subscription): number
}
```

**사용 예시**
```typescript
import { subscriptionService } from './services/subscriptionService';

// 구독 조회
const subscription = await subscriptionService.getUserSubscription('user123');

// 구독 취소
await subscriptionService.cancelSubscription('user123');

// 활성 상태 확인
const isActive = await subscriptionService.isSubscriptionActive('user123');
```

---

## Firestore Data Models

### Subscription

```typescript
interface Subscription {
  userId: string;
  planId: 'free' | 'starter' | 'pro';
  status: 'active' | 'cancelled' | 'expired' | 'pending';
  startDate: Date;
  endDate: Date;
  paymentKey?: string;
  orderId?: string;
  amount: number;
  autoRenew: boolean;
  cancelledAt?: Date;
  createdAt: Date;
  updatedAt: Date;
}
```

### PaymentHistory

```typescript
interface PaymentHistory {
  id: string;
  userId: string;
  orderId: string;
  paymentKey: string;
  amount: number;
  planId: 'free' | 'starter' | 'pro';
  status: 'completed' | 'failed' | 'cancelled' | 'refunded';
  paymentMethod: string;
  paidAt: Date;
  refundedAt?: Date;
  metadata?: Record<string, any>;
}
```

### SubscriptionPlan

```typescript
interface SubscriptionPlan {
  id: 'free' | 'starter' | 'pro';
  name: string;
  nameKo: string;
  price: number;
  billingCycle: 'monthly' | 'yearly';
  features: string[];
  featuresKo: string[];
  limits: {
    atsAnalysis: number | 'unlimited';
    templates: number | 'unlimited';
    aiPhotoAnalysis: boolean;
    voiceInterview: boolean;
    consulting: boolean;
    keywordOptimization: boolean;
  };
  popular?: boolean;
}
```

---

## 에러 코드

### 토스페이먼츠 에러

| 코드 | 설명 |
|------|------|
| `CARD_DECLINED` | 카드 승인 거부 |
| `INSUFFICIENT_BALANCE` | 잔액 부족 |
| `INVALID_CARD_NUMBER` | 유효하지 않은 카드 번호 |
| `EXPIRED_CARD` | 만료된 카드 |
| `INVALID_CVC` | 잘못된 CVC |
| `EXCEED_MAX_CARD_QUOTA` | 카드 한도 초과 |
| `USER_CANCEL` | 사용자 취소 |
| `PAYMENT_TIMEOUT` | 결제 시간 초과 |

### Firebase 에러

| 코드 | 설명 |
|------|------|
| `permission-denied` | 권한 없음 |
| `unauthenticated` | 인증 필요 |
| `not-found` | 리소스 없음 |
| `already-exists` | 이미 존재함 |
| `failed-precondition` | 사전 조건 미충족 |

---

## Webhook 이벤트

### 결제 상태 변경
```json
{
  "eventType": "PAYMENT_STATUS_CHANGED",
  "data": {
    "paymentKey": "payment_key_123",
    "orderId": "ORDER_123",
    "status": "DONE",
    "amount": 9900
  }
}
```

### 결제 취소
```json
{
  "eventType": "PAYMENT_CANCELED",
  "data": {
    "paymentKey": "payment_key_123",
    "orderId": "ORDER_123",
    "canceledAt": "2024-01-15T10:00:00+09:00"
  }
}
```

### 환불 완료
```json
{
  "eventType": "PAYMENT_REFUNDED",
  "data": {
    "paymentKey": "payment_key_123",
    "orderId": "ORDER_123",
    "refundedAt": "2024-01-15T10:00:00+09:00"
  }
}
```

---

## Rate Limiting

| 엔드포인트 | 제한 |
|-----------|------|
| `confirmTossPayment` | 10 요청/분 |
| `refundPayment` | 5 요청/분 |
| `renewSubscription` | 3 요청/분 |

---

## 테스트 환경

### 테스트 API 키
```
Client Key: test_ck_XXXXXXXXXXXXXXXXXXXXXXXX
Secret Key: test_sk_XXXXXXXXXXXXXXXXXXXXXXXX
```

### 테스트 카드
```
카드번호: 4330-1234-5678-9012
유효기간: 12/25
CVC: 123
비밀번호: 00
```

---

## 지원

API 관련 문의: api-support@airesume.com
