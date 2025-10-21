/**
 * Toss Payments Webhook Handler
 * 토스페이먼츠 웹훅 처리
 */

import * as functions from 'firebase-functions';
import * as admin from 'firebase-admin';
import * as crypto from 'crypto';

interface WebhookEvent {
  eventType: string;
  data: {
    paymentKey: string;
    orderId: string;
    status: string;
    amount: number;
    method: string;
    approvedAt?: string;
    canceledAt?: string;
    refundedAt?: string;
  };
  createdAt: string;
}

export const handlePaymentWebhook = functions.https.onRequest(async (req, res) => {
  try {
    // POST 메서드만 허용
    if (req.method !== 'POST') {
      res.status(405).send('Method Not Allowed');
      return;
    }

    const event: WebhookEvent = req.body;
    const db = admin.firestore();

    functions.logger.info('웹훅 수신', { event });

    // 이벤트 타입별 처리
    switch (event.eventType) {
      case 'PAYMENT_STATUS_CHANGED':
        await handlePaymentStatusChanged(db, event);
        break;

      case 'PAYMENT_CANCELED':
        await handlePaymentCanceled(db, event);
        break;

      case 'PAYMENT_REFUNDED':
        await handlePaymentRefunded(db, event);
        break;

      case 'SUBSCRIPTION_RENEWED':
        await handleSubscriptionRenewed(db, event);
        break;

      default:
        functions.logger.warn('알 수 없는 이벤트 타입', {
          eventType: event.eventType,
        });
    }

    res.status(200).json({ success: true });
  } catch (error: any) {
    functions.logger.error('웹훅 처리 실패', { error: error.message });
    res.status(500).json({ success: false, error: error.message });
  }
});

/**
 * 결제 상태 변경 처리
 */
async function handlePaymentStatusChanged(
  db: admin.firestore.Firestore,
  event: WebhookEvent
): Promise<void> {
  const { orderId, status } = event.data;

  // 결제 이력 업데이트
  const paymentQuery = await db
    .collection('paymentHistory')
    .where('orderId', '==', orderId)
    .limit(1)
    .get();

  if (!paymentQuery.empty) {
    const paymentDoc = paymentQuery.docs[0];
    await paymentDoc.ref.update({
      status: status.toLowerCase(),
      updatedAt: admin.firestore.Timestamp.now(),
    });
  }

  functions.logger.info('결제 상태 업데이트 완료', { orderId, status });
}

/**
 * 결제 취소 처리
 */
async function handlePaymentCanceled(
  db: admin.firestore.Firestore,
  event: WebhookEvent
): Promise<void> {
  const { orderId, canceledAt } = event.data;

  // 결제 이력 업데이트
  const paymentQuery = await db
    .collection('paymentHistory')
    .where('orderId', '==', orderId)
    .limit(1)
    .get();

  if (!paymentQuery.empty) {
    const paymentDoc = paymentQuery.docs[0];
    const paymentData = paymentDoc.data();

    await paymentDoc.ref.update({
      status: 'cancelled',
      canceledAt: canceledAt
        ? admin.firestore.Timestamp.fromDate(new Date(canceledAt))
        : admin.firestore.Timestamp.now(),
      updatedAt: admin.firestore.Timestamp.now(),
    });

    // 구독 취소
    if (paymentData.userId) {
      await db
        .collection('subscriptions')
        .doc(paymentData.userId)
        .update({
          status: 'cancelled',
          autoRenew: false,
          cancelledAt: admin.firestore.Timestamp.now(),
          updatedAt: admin.firestore.Timestamp.now(),
        });
    }
  }

  functions.logger.info('결제 취소 처리 완료', { orderId });
}

/**
 * 환불 처리
 */
async function handlePaymentRefunded(
  db: admin.firestore.Firestore,
  event: WebhookEvent
): Promise<void> {
  const { orderId, refundedAt } = event.data;

  // 결제 이력 업데이트
  const paymentQuery = await db
    .collection('paymentHistory')
    .where('orderId', '==', orderId)
    .limit(1)
    .get();

  if (!paymentQuery.empty) {
    const paymentDoc = paymentQuery.docs[0];
    await paymentDoc.ref.update({
      status: 'refunded',
      refundedAt: refundedAt
        ? admin.firestore.Timestamp.fromDate(new Date(refundedAt))
        : admin.firestore.Timestamp.now(),
      updatedAt: admin.firestore.Timestamp.now(),
    });
  }

  functions.logger.info('환불 처리 완료', { orderId });
}

/**
 * 구독 갱신 처리
 */
async function handleSubscriptionRenewed(
  db: admin.firestore.Firestore,
  event: WebhookEvent
): Promise<void> {
  const { orderId, paymentKey, amount } = event.data;

  // 결제 이력에서 사용자 정보 조회
  const paymentQuery = await db
    .collection('paymentHistory')
    .where('orderId', '==', orderId)
    .limit(1)
    .get();

  if (!paymentQuery.empty) {
    const paymentData = paymentQuery.docs[0].data();
    const userId = paymentData.userId;

    // 구독 연장
    const subscriptionRef = db.collection('subscriptions').doc(userId);
    const subscription = await subscriptionRef.get();

    if (subscription.exists) {
      const currentEndDate = subscription.data()!.endDate.toDate();
      const newEndDate = new Date(currentEndDate);
      newEndDate.setMonth(newEndDate.getMonth() + 1);

      await subscriptionRef.update({
        endDate: admin.firestore.Timestamp.fromDate(newEndDate),
        updatedAt: admin.firestore.Timestamp.now(),
      });

      // 새 결제 이력 추가
      await db.collection('paymentHistory').add({
        userId,
        orderId,
        paymentKey,
        amount,
        planId: paymentData.planId,
        status: 'completed',
        paymentMethod: 'auto_renewal',
        paidAt: admin.firestore.Timestamp.now(),
      });

      functions.logger.info('구독 갱신 완료', { userId, newEndDate });
    }
  }
}
