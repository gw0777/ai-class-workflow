/**
 * Toss Payments Service
 * 토스페이먼츠 결제 서비스
 */

import { loadTossPayments, TossPaymentsInstance } from '@tosspayments/payment-sdk';
import { tossConfig, generateOrderId, generateCustomerKey } from '../config/tossConfig';
import { PlanType, getPlanPrice } from '../config/subscriptionPlans';

export interface PaymentRequest {
  planId: PlanType;
  userId: string;
  userName: string;
  userEmail: string;
  customAmount?: number; // 커스텀 금액 (일회성 결제)
}

export interface PaymentResult {
  success: boolean;
  orderId?: string;
  paymentKey?: string;
  error?: string;
}

class TossPaymentService {
  private tossPayments: TossPaymentsInstance | null = null;

  /**
   * Toss Payments SDK 초기화
   */
  async initialize(): Promise<void> {
    if (!this.tossPayments) {
      this.tossPayments = await loadTossPayments(tossConfig.clientKey);
    }
  }

  /**
   * 정기 결제 요청 (구독)
   */
  async requestSubscriptionPayment(request: PaymentRequest): Promise<void> {
    await this.initialize();

    if (!this.tossPayments) {
      throw new Error('Toss Payments SDK가 초기화되지 않았습니다.');
    }

    const amount = request.customAmount || getPlanPrice(request.planId);
    const orderId = generateOrderId();
    const customerKey = generateCustomerKey(request.userId);

    try {
      await this.tossPayments.requestPayment('카드', {
        amount,
        orderId,
        orderName: `AI Resume Master ${request.planId.toUpperCase()} 구독`,
        customerName: request.userName,
        customerEmail: request.userEmail,
        customerKey, // 자동결제를 위한 고객 키
        successUrl: tossConfig.successUrl,
        failUrl: tossConfig.failUrl,
      });
    } catch (error) {
      console.error('결제 요청 실패:', error);
      throw error;
    }
  }

  /**
   * 일회성 결제 요청
   */
  async requestOneTimePayment(request: PaymentRequest): Promise<void> {
    await this.initialize();

    if (!this.tossPayments) {
      throw new Error('Toss Payments SDK가 초기화되지 않았습니다.');
    }

    const amount = request.customAmount || getPlanPrice(request.planId);
    const orderId = generateOrderId();

    try {
      await this.tossPayments.requestPayment('카드', {
        amount,
        orderId,
        orderName: `AI Resume Master - 일회성 분석`,
        customerName: request.userName,
        customerEmail: request.userEmail,
        successUrl: tossConfig.successUrl,
        failUrl: tossConfig.failUrl,
      });
    } catch (error) {
      console.error('결제 요청 실패:', error);
      throw error;
    }
  }

  /**
   * 간편결제 (계좌이체)
   */
  async requestTransferPayment(request: PaymentRequest): Promise<void> {
    await this.initialize();

    if (!this.tossPayments) {
      throw new Error('Toss Payments SDK가 초기화되지 않았습니다.');
    }

    const amount = request.customAmount || getPlanPrice(request.planId);
    const orderId = generateOrderId();

    try {
      await this.tossPayments.requestPayment('계좌이체', {
        amount,
        orderId,
        orderName: `AI Resume Master ${request.planId.toUpperCase()} 구독`,
        customerName: request.userName,
        customerEmail: request.userEmail,
        successUrl: tossConfig.successUrl,
        failUrl: tossConfig.failUrl,
      });
    } catch (error) {
      console.error('계좌이체 결제 실패:', error);
      throw error;
    }
  }

  /**
   * 결제 정보 조회 (URL 파라미터에서)
   */
  getPaymentInfoFromUrl(): {
    paymentKey: string | null;
    orderId: string | null;
    amount: string | null;
  } {
    const urlParams = new URLSearchParams(window.location.search);
    return {
      paymentKey: urlParams.get('paymentKey'),
      orderId: urlParams.get('orderId'),
      amount: urlParams.get('amount'),
    };
  }

  /**
   * 결제 실패 정보 조회
   */
  getPaymentFailInfo(): {
    code: string | null;
    message: string | null;
  } {
    const urlParams = new URLSearchParams(window.location.search);
    return {
      code: urlParams.get('code'),
      message: urlParams.get('message'),
    };
  }
}

export const tossPaymentService = new TossPaymentService();
