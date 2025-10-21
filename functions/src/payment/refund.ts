/**
 * Refund Payment
 * 결제 환불 처리
 */

import * as functions from 'firebase-functions';
import * as admin from 'firebase-admin';
import axios from 'axios';

interface RefundRequest {
  paymentKey: string;
  cancelReason: string;
  refundAmount?: number; // 부분 환불 금액 (선택)
}

interface RefundResponse {
  success: boolean;
  refundId?: string;
  error?: string;
}

const TOSS_CANCEL_URL = 'https://api.tosspayments.com/v1/payments';

export const refundPayment = functions.https.onCall(
  async (
    data: RefundRequest,
    context: functions.https.CallableContext
  ): Promise<RefundResponse> => {
    try {
      // 관리자 권한 확인
      if (!context.auth) {
        throw new functions.https.HttpsError(
          'unauthenticated',
          '인증이 필요합니다.'
        );
      }

      // 관리자 권한 체크 (실제 환경에서는 Custom Claims 사용)
      const userDoc = await admin
        .firestore()
        .collection('users')
        .doc(context.auth.uid)
        .get();

      if (!userDoc.exists || !userDoc.data()?.isAdmin) {
        throw new functions.https.HttpsError(
          'permission-denied',
          '관리자 권한이 필요합니다.'
        );
      }

      const { paymentKey, cancelReason, refundAmount } = data;

      // 토스페이먼츠 API로 환불 요청
      const secretKey = functions.config().toss.secret_key;
      const encodedKey = Buffer.from(`${secretKey}:`).toString('base64');

      const cancelData: any = {
        cancelReason,
      };

      if (refundAmount) {
        cancelData.cancelAmount = refundAmount;
      }

      const tossResponse = await axios.post(
        `${TOSS_CANCEL_URL}/${paymentKey}/cancel`,
        cancelData,
        {
          headers: {
            Authorization: `Basic ${encodedKey}`,
            'Content-Type': 'application/json',
          },
        }
      );

      // Firestore 업데이트
      const db = admin.firestore();
      const paymentQuery = await db
        .collection('paymentHistory')
        .where('paymentKey', '==', paymentKey)
        .limit(1)
        .get();

      if (!paymentQuery.empty) {
        const paymentDoc = paymentQuery.docs[0];
        await paymentDoc.ref.update({
          status: 'refunded',
          refundedAt: admin.firestore.Timestamp.now(),
          refundAmount: refundAmount || paymentDoc.data().amount,
          cancelReason,
          updatedAt: admin.firestore.Timestamp.now(),
        });

        // 구독 상태 업데이트
        const userId = paymentDoc.data().userId;
        await db
          .collection('subscriptions')
          .doc(userId)
          .update({
            status: 'cancelled',
            autoRenew: false,
            updatedAt: admin.firestore.Timestamp.now(),
          });
      }

      functions.logger.info('환불 처리 완료', {
        paymentKey,
        refundAmount,
        cancelReason,
      });

      return {
        success: true,
        refundId: tossResponse.data.cancelId,
      };
    } catch (error: any) {
      functions.logger.error('환불 처리 실패', {
        error: error.message,
        data,
      });

      return {
        success: false,
        error: error.response?.data?.message || error.message,
      };
    }
  }
);
