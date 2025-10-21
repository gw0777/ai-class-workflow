/**
 * Subscription Status Component
 * 구독 상태 표시 컴포넌트
 */

import React, { useEffect, useState } from 'react';
import { Calendar, CreditCard, AlertCircle } from 'lucide-react';
import { subscriptionService, Subscription } from '../../services/subscriptionService';
import { subscriptionPlans } from '../../config/subscriptionPlans';

interface SubscriptionStatusProps {
  userId: string;
}

export const SubscriptionStatus: React.FC<SubscriptionStatusProps> = ({ userId }) => {
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [loading, setLoading] = useState(true);
  const [cancelling, setCancelling] = useState(false);

  useEffect(() => {
    loadSubscription();
  }, [userId]);

  const loadSubscription = async () => {
    try {
      const sub = await subscriptionService.getUserSubscription(userId);
      setSubscription(sub);
    } catch (error) {
      console.error('구독 정보 로드 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCancelSubscription = async () => {
    if (!subscription) return;

    const confirmed = window.confirm(
      '구독을 취소하시겠습니까? 현재 기간 종료까지는 계속 이용하실 수 있습니다.'
    );

    if (!confirmed) return;

    setCancelling(true);
    try {
      await subscriptionService.cancelSubscription(userId);
      await loadSubscription();
      alert('구독이 취소되었습니다.');
    } catch (error) {
      alert('구독 취소에 실패했습니다.');
      console.error('구독 취소 실패:', error);
    } finally {
      setCancelling(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="h-8 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>
    );
  }

  if (!subscription) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
        <div className="flex items-start">
          <AlertCircle className="w-5 h-5 text-yellow-600 mr-3 mt-0.5" />
          <div>
            <h3 className="font-semibold text-yellow-900">구독 정보 없음</h3>
            <p className="text-sm text-yellow-700 mt-1">
              현재 활성화된 구독이 없습니다. 플랜을 선택하여 시작하세요.
            </p>
          </div>
        </div>
      </div>
    );
  }

  const plan = subscriptionPlans[subscription.planId];
  const daysLeft = subscriptionService.getDaysUntilExpiration(subscription);
  const isExpiring = daysLeft <= 7;

  const formatDate = (date: Date): string => {
    return new Intl.DateTimeFormat('ko-KR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    }).format(date);
  };

  const getStatusBadge = () => {
    const statusConfig = {
      active: { color: 'green', text: '활성' },
      cancelled: { color: 'red', text: '취소됨' },
      expired: { color: 'gray', text: '만료됨' },
      pending: { color: 'yellow', text: '대기 중' },
    };

    const config = statusConfig[subscription.status];

    return (
      <span
        className={`
          px-3 py-1 rounded-full text-xs font-semibold
          bg-${config.color}-100 text-${config.color}-700
        `}
      >
        {config.text}
      </span>
    );
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-gray-900">구독 정보</h2>
        {getStatusBadge()}
      </div>

      {/* 플랜 정보 */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-2xl font-bold text-gray-900">{plan.nameKo}</h3>
            <p className="text-sm text-gray-500 mt-1">{plan.name} Plan</p>
          </div>
          <div className="text-right">
            <p className="text-2xl font-bold text-blue-600">
              {new Intl.NumberFormat('ko-KR', {
                style: 'currency',
                currency: 'KRW',
              }).format(subscription.amount)}
            </p>
            <p className="text-sm text-gray-500">/ 월</p>
          </div>
        </div>
      </div>

      {/* 구독 기간 */}
      <div className="space-y-3 mb-6">
        <div className="flex items-center text-sm">
          <Calendar className="w-4 h-4 text-gray-400 mr-2" />
          <span className="text-gray-600">시작일:</span>
          <span className="ml-2 font-medium text-gray-900">
            {formatDate(subscription.startDate)}
          </span>
        </div>
        <div className="flex items-center text-sm">
          <Calendar className="w-4 h-4 text-gray-400 mr-2" />
          <span className="text-gray-600">종료일:</span>
          <span className="ml-2 font-medium text-gray-900">
            {formatDate(subscription.endDate)}
          </span>
        </div>
        <div className="flex items-center text-sm">
          <CreditCard className="w-4 h-4 text-gray-400 mr-2" />
          <span className="text-gray-600">자동 갱신:</span>
          <span className="ml-2 font-medium text-gray-900">
            {subscription.autoRenew ? '활성화' : '비활성화'}
          </span>
        </div>
      </div>

      {/* 만료 경고 */}
      {isExpiring && subscription.status === 'active' && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
          <p className="text-sm text-yellow-800">
            구독이 {daysLeft}일 후 만료됩니다.
            {!subscription.autoRenew && ' 자동 갱신이 비활성화되어 있습니다.'}
          </p>
        </div>
      )}

      {/* 액션 버튼 */}
      {subscription.status === 'active' && subscription.autoRenew && (
        <button
          onClick={handleCancelSubscription}
          disabled={cancelling}
          className={`
            w-full py-3 rounded-lg font-semibold transition-all
            ${
              cancelling
                ? 'bg-gray-400 text-white cursor-wait'
                : 'bg-red-50 text-red-600 hover:bg-red-100'
            }
          `}
        >
          {cancelling ? '처리 중...' : '구독 취소'}
        </button>
      )}
    </div>
  );
};
