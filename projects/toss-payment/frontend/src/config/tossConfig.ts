/**
 * Toss Payments Configuration
 * 토스페이먼츠 결제 설정
 */

export const tossConfig = {
  // 클라이언트 키 (공개 키)
  clientKey: import.meta.env.VITE_TOSS_CLIENT_KEY,

  // 결제 성공/실패 리다이렉트 URL
  successUrl: `${import.meta.env.VITE_APP_URL}/payment/success`,
  failUrl: `${import.meta.env.VITE_APP_URL}/payment/fail`,

  // 지원 결제 방법
  paymentMethods: {
    card: '카드',
    transfer: '계좌이체',
    virtualAccount: '가상계좌',
    mobilePhone: '휴대폰',
  },

  // 기본 설정
  defaults: {
    currency: 'KRW',
    locale: 'ko_KR',
  },
};

/**
 * 결제 금액 검증
 */
export const validatePaymentAmount = (amount: number): boolean => {
  return amount > 0 && amount <= 10000000; // 최대 천만원
};

/**
 * 주문 ID 생성
 */
export const generateOrderId = (): string => {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substring(2, 9);
  return `ORDER_${timestamp}_${random}`;
};

/**
 * 고객 키 생성 (사용자 ID 기반)
 */
export const generateCustomerKey = (userId: string): string => {
  return `CUSTOMER_${userId}`;
};
