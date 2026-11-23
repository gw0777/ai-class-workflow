/**
 * Check Expired Subscriptions
 * 만료된 구독 확인 및 처리 (스케줄러)
 */

import * as functions from 'firebase-functions';
import * as admin from 'firebase-admin';

/**
 * 매일 자정에 실행되는 스케줄 함수
 * 만료된 구독을 확인하고 상태를 업데이트합니다.
 */
export const checkExpiredSubscriptions = functions.pubsub
  .schedule('0 0 * * *') // 매일 자정 (한국 시간 기준으로 조정 필요)
  .timeZone('Asia/Seoul')
  .onRun(async (context) => {
    const db = admin.firestore();
    const now = admin.firestore.Timestamp.now();

    try {
      // 활성 상태이지만 만료된 구독 조회
      const expiredQuery = await db
        .collection('subscriptions')
        .where('status', '==', 'active')
        .where('endDate', '<', now)
        .get();

      if (expiredQuery.empty) {
        functions.logger.info('만료된 구독 없음');
        return null;
      }

      // 배치 업데이트
      const batch = db.batch();
      let count = 0;

      expiredQuery.forEach((doc) => {
        batch.update(doc.ref, {
          status: 'expired',
          autoRenew: false,
          updatedAt: now,
        });
        count++;
      });

      await batch.commit();

      functions.logger.info('만료된 구독 처리 완료', { count });

      // 만료 알림 전송 (선택 사항)
      await sendExpirationNotifications(expiredQuery.docs);

      return null;
    } catch (error: any) {
      functions.logger.error('만료 구독 확인 실패', { error: error.message });
      throw error;
    }
  });

/**
 * 만료 알림 전송
 */
async function sendExpirationNotifications(
  subscriptions: admin.firestore.QueryDocumentSnapshot[]
): Promise<void> {
  const db = admin.firestore();

  for (const subscriptionDoc of subscriptions) {
    const subscription = subscriptionDoc.data();
    const userId = subscription.userId;

    try {
      // 사용자 정보 조회
      const userDoc = await db.collection('users').doc(userId).get();
      if (!userDoc.exists) continue;

      const userData = userDoc.data();
      const userEmail = userData?.email;

      if (userEmail) {
        // 이메일 알림 큐에 추가
        await db.collection('emailQueue').add({
          to: userEmail,
          template: 'subscription_expired',
          data: {
            userName: userData?.name || '사용자',
            planName: subscription.planId,
            expiredDate: subscription.endDate.toDate().toLocaleDateString('ko-KR'),
          },
          status: 'pending',
          createdAt: admin.firestore.Timestamp.now(),
        });

        functions.logger.info('만료 알림 생성', { userId, email: userEmail });
      }
    } catch (error: any) {
      functions.logger.error('알림 전송 실패', { userId, error: error.message });
    }
  }
}
