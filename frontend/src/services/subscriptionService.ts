/**
 * Subscription Service
 * 구독 관리 서비스
 */

import {
  collection,
  doc,
  getDoc,
  setDoc,
  updateDoc,
  query,
  where,
  getDocs,
  Timestamp,
} from 'firebase/firestore';
import { db } from './firebaseService';
import { PlanType } from '../config/subscriptionPlans';

export interface Subscription {
  userId: string;
  planId: PlanType;
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

export interface PaymentHistory {
  id: string;
  userId: string;
  orderId: string;
  paymentKey: string;
  amount: number;
  planId: PlanType;
  status: 'completed' | 'failed' | 'cancelled' | 'refunded';
  paymentMethod: string;
  paidAt: Date;
  refundedAt?: Date;
  metadata?: Record<string, any>;
}

class SubscriptionService {
  private readonly SUBSCRIPTIONS_COLLECTION = 'subscriptions';
  private readonly PAYMENT_HISTORY_COLLECTION = 'paymentHistory';

  /**
   * 사용자의 현재 구독 정보 조회
   */
  async getUserSubscription(userId: string): Promise<Subscription | null> {
    try {
      const docRef = doc(db, this.SUBSCRIPTIONS_COLLECTION, userId);
      const docSnap = await getDoc(docRef);

      if (docSnap.exists()) {
        const data = docSnap.data();
        return {
          ...data,
          startDate: data.startDate.toDate(),
          endDate: data.endDate.toDate(),
          cancelledAt: data.cancelledAt?.toDate(),
          createdAt: data.createdAt.toDate(),
          updatedAt: data.updatedAt.toDate(),
        } as Subscription;
      }

      return null;
    } catch (error) {
      console.error('구독 정보 조회 실패:', error);
      throw error;
    }
  }

  /**
   * 구독 생성
   */
  async createSubscription(subscription: Omit<Subscription, 'createdAt' | 'updatedAt'>): Promise<void> {
    try {
      const now = Timestamp.now();
      const docRef = doc(db, this.SUBSCRIPTIONS_COLLECTION, subscription.userId);

      await setDoc(docRef, {
        ...subscription,
        startDate: Timestamp.fromDate(subscription.startDate),
        endDate: Timestamp.fromDate(subscription.endDate),
        cancelledAt: subscription.cancelledAt ? Timestamp.fromDate(subscription.cancelledAt) : null,
        createdAt: now,
        updatedAt: now,
      });
    } catch (error) {
      console.error('구독 생성 실패:', error);
      throw error;
    }
  }

  /**
   * 구독 업데이트
   */
  async updateSubscription(userId: string, updates: Partial<Subscription>): Promise<void> {
    try {
      const docRef = doc(db, this.SUBSCRIPTIONS_COLLECTION, userId);
      const updateData: any = {
        ...updates,
        updatedAt: Timestamp.now(),
      };

      // Date 객체를 Timestamp로 변환
      if (updates.startDate) {
        updateData.startDate = Timestamp.fromDate(updates.startDate);
      }
      if (updates.endDate) {
        updateData.endDate = Timestamp.fromDate(updates.endDate);
      }
      if (updates.cancelledAt) {
        updateData.cancelledAt = Timestamp.fromDate(updates.cancelledAt);
      }

      await updateDoc(docRef, updateData);
    } catch (error) {
      console.error('구독 업데이트 실패:', error);
      throw error;
    }
  }

  /**
   * 구독 취소
   */
  async cancelSubscription(userId: string): Promise<void> {
    try {
      await this.updateSubscription(userId, {
        status: 'cancelled',
        autoRenew: false,
        cancelledAt: new Date(),
      });
    } catch (error) {
      console.error('구독 취소 실패:', error);
      throw error;
    }
  }

  /**
   * 결제 이력 저장
   */
  async savePaymentHistory(payment: Omit<PaymentHistory, 'id'>): Promise<void> {
    try {
      const docRef = doc(collection(db, this.PAYMENT_HISTORY_COLLECTION));
      await setDoc(docRef, {
        ...payment,
        paidAt: Timestamp.fromDate(payment.paidAt),
        refundedAt: payment.refundedAt ? Timestamp.fromDate(payment.refundedAt) : null,
      });
    } catch (error) {
      console.error('결제 이력 저장 실패:', error);
      throw error;
    }
  }

  /**
   * 사용자의 결제 이력 조회
   */
  async getUserPaymentHistory(userId: string): Promise<PaymentHistory[]> {
    try {
      const q = query(
        collection(db, this.PAYMENT_HISTORY_COLLECTION),
        where('userId', '==', userId)
      );

      const querySnapshot = await getDocs(q);
      return querySnapshot.docs.map((doc) => {
        const data = doc.data();
        return {
          id: doc.id,
          ...data,
          paidAt: data.paidAt.toDate(),
          refundedAt: data.refundedAt?.toDate(),
        } as PaymentHistory;
      });
    } catch (error) {
      console.error('결제 이력 조회 실패:', error);
      throw error;
    }
  }

  /**
   * 구독 활성화 여부 확인
   */
  async isSubscriptionActive(userId: string): Promise<boolean> {
    const subscription = await this.getUserSubscription(userId);
    if (!subscription) return false;

    const now = new Date();
    return subscription.status === 'active' && subscription.endDate > now;
  }

  /**
   * 구독 만료 일수 계산
   */
  getDaysUntilExpiration(subscription: Subscription): number {
    const now = new Date();
    const diffTime = subscription.endDate.getTime() - now.getTime();
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  }
}

export const subscriptionService = new SubscriptionService();
