/**
 * Confirm Toss Payment
 * 토스 결제 승인 처리
 */

import * as functions from 'firebase-functions';
import * as admin from 'firebase-admin';
import axios from 'axios';

interface ConfirmPaymentRequest {
  paymentKey: string;
  orderId: string;
  amount: number;
  userId: string;
  planId: string;
}

interface ConfirmPaymentResponse {
  success: boolean;
  subscription?: any;
  error?: string;
}

const TOSS_API_URL = 'https://api.tosspayments.com/v1/payments/confirm';

export const confirmTossPayment = functions.https.onCall(
  async (
    data: ConfirmPaymentRequest,
    context: functions.https.CallableContext
  ): Promise<ConfirmPaymentResponse> => {
    try {
      // 인증 확인
      if (!context.auth) {
        throw new functions.https.HttpsError(
          'unauthenticated',
          '인증이 필요합니다.'
        );
      }

      // 사용자 ID 검증
      if (context.auth.uid !== data.userId) {
        throw new functions.https.HttpsError(
          'permission-denied',
          '권한이 없습니다.'
        );
      }

      const { paymentKey, orderId, amount, userId, planId } = data;

      // 토스페이먼츠 API로 결제 승인 요청
      const secretKey = functions.config().toss.secret_key;
      const encodedKey = Buffer.from(`${secretKey}:`).toString('base64');

      const tossResponse = await axios.post(
        TOSS_API_URL,
        {
          paymentKey,
          orderId,
          amount,
        },
        {
          headers: {
            Authorization: `Basic ${encodedKey}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (tossResponse.data.status !== 'DONE') {
        throw new Error('결제 승인 실패');
      }

      // Firestore에 구독 정보 저장
      const db = admin.firestore();
      const now = admin.firestore.Timestamp.now();
      const startDate = new Date();
      const endDate = new Date();
      endDate.setMonth(endDate.getMonth() + 1); // 1개월 후

      const subscriptionData = {
        userId,
        planId,
        status: 'active',
        startDate: admin.firestore.Timestamp.fromDate(startDate),
        endDate: admin.firestore.Timestamp.fromDate(endDate),
        paymentKey,
        orderId,
        amount,
        autoRenew: true,
        createdAt: now,
        updatedAt: now,
      };

      await db
        .collection('subscriptions')
        .doc(userId)
        .set(subscriptionData);

      // 결제 이력 저장
      await db.collection('paymentHistory').add({
        userId,
        orderId,
        paymentKey,
        amount,
        planId,
        status: 'completed',
        paymentMethod: tossResponse.data.method,
        paidAt: now,
        metadata: {
          tossPaymentId: tossResponse.data.paymentId,
          approvedAt: tossResponse.data.approvedAt,
        },
      });

      functions.logger.info('결제 승인 완료', {
        userId,
        orderId,
        amount,
        planId,
      });

      return {
        success: true,
        subscription: subscriptionData,
      };
    } catch (error: any) {
      functions.logger.error('결제 승인 실패', {
        error: error.message,
        data,
      });

      return {
        success: false,
        error: error.message || '결제 처리 중 오류가 발생했습니다.',
      };
    }
  }
);
