/**
 * Renew Subscription
 * 구독 갱신 처리
 */

import * as functions from 'firebase-functions';
import * as admin from 'firebase-admin';
import axios from 'axios';

interface RenewRequest {
  userId: string;
}

interface RenewResponse {
  success: boolean;
  subscription?: any;
  error?: string;
}

const TOSS_BILLING_URL = 'https://api.tosspayments.com/v1/billing';

export const renewSubscription = functions.https.onCall(
  async (
    data: RenewRequest,
    context: functions.https.CallableContext
  ): Promise<RenewResponse> => {
    try {
      // 인증 확인
      if (!context.auth || context.auth.uid !== data.userId) {
        throw new functions.https.HttpsError(
          'permission-denied',
          '권한이 없습니다.'
        );
      }

      const { userId } = data;
      const db = admin.firestore();

      // 현재 구독 정보 조회
      const subscriptionDoc = await db
        .collection('subscriptions')
        .doc(userId)
        .get();

      if (!subscriptionDoc.exists) {
        throw new functions.https.HttpsError(
          'not-found',
          '구독 정보를 찾을 수 없습니다.'
        );
      }

      const subscription = subscriptionDoc.data()!;

      // 자동 갱신이 비활성화된 경우
      if (!subscription.autoRenew) {
        throw new functions.https.HttpsError(
          'failed-precondition',
          '자동 갱신이 비활성화되어 있습니다.'
        );
      }

      // 사용자 정보 조회 (빌링키 확인)
      const userDoc = await db.collection('users').doc(userId).get();
      const billingKey = userDoc.data()?.billingKey;

      if (!billingKey) {
        throw new functions.https.HttpsError(
          'failed-precondition',
          '등록된 결제 수단이 없습니다.'
        );
      }

      // 토스페이먼츠 자동결제 요청
      const secretKey = functions.config().toss.secret_key;
      const encodedKey = Buffer.from(`${secretKey}:`).toString('base64');

      const orderId = `AUTO_${Date.now()}_${userId}`;
      const amount = subscription.amount;

      const billingResponse = await axios.post(
        `${TOSS_BILLING_URL}/${billingKey}`,
        {
          customerKey: `CUSTOMER_${userId}`,
          amount,
          orderId,
          orderName: `AI Resume Master ${subscription.planId} 자동갱신`,
        },
        {
          headers: {
            Authorization: `Basic ${encodedKey}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (billingResponse.data.status !== 'DONE') {
        throw new Error('자동결제 실패');
      }

      // 구독 기간 연장
      const currentEndDate = subscription.endDate.toDate();
      const newEndDate = new Date(currentEndDate);
      newEndDate.setMonth(newEndDate.getMonth() + 1);

      const updatedSubscription = {
        endDate: admin.firestore.Timestamp.fromDate(newEndDate),
        status: 'active',
        updatedAt: admin.firestore.Timestamp.now(),
      };

      await subscriptionDoc.ref.update(updatedSubscription);

      // 결제 이력 저장
      await db.collection('paymentHistory').add({
        userId,
        orderId,
        paymentKey: billingResponse.data.paymentKey,
        amount,
        planId: subscription.planId,
        status: 'completed',
        paymentMethod: 'auto_renewal',
        paidAt: admin.firestore.Timestamp.now(),
        metadata: {
          tossPaymentId: billingResponse.data.paymentId,
          billingKey,
        },
      });

      functions.logger.info('구독 갱신 완료', {
        userId,
        newEndDate,
        amount,
      });

      return {
        success: true,
        subscription: {
          ...subscription,
          ...updatedSubscription,
        },
      };
    } catch (error: any) {
      functions.logger.error('구독 갱신 실패', {
        error: error.message,
        data,
      });

      // 갱신 실패 시 구독 상태 업데이트
      if (data.userId) {
        const db = admin.firestore();
        await db
          .collection('subscriptions')
          .doc(data.userId)
          .update({
            status: 'expired',
            autoRenew: false,
            updatedAt: admin.firestore.Timestamp.now(),
          });
      }

      return {
        success: false,
        error: error.message || '구독 갱신에 실패했습니다.',
      };
    }
  }
);
