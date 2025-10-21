/**
 * Pricing Card Component
 * 요금제 카드 컴포넌트
 */

import React from 'react';
import { Check } from 'lucide-react';
import { SubscriptionPlan } from '../../config/subscriptionPlans';

interface PricingCardProps {
  plan: SubscriptionPlan;
  currentPlan?: string;
  onSelectPlan: (planId: string) => void;
  loading?: boolean;
}

export const PricingCard: React.FC<PricingCardProps> = ({
  plan,
  currentPlan,
  onSelectPlan,
  loading = false,
}) => {
  const isCurrent = currentPlan === plan.id;
  const isPopular = plan.popular;

  const formatPrice = (price: number): string => {
    return new Intl.NumberFormat('ko-KR', {
      style: 'currency',
      currency: 'KRW',
    }).format(price);
  };

  return (
    <div
      className={`
        relative rounded-2xl border-2 p-8 shadow-lg transition-all hover:shadow-xl
        ${isPopular ? 'border-blue-500 scale-105' : 'border-gray-200'}
        ${isCurrent ? 'bg-blue-50' : 'bg-white'}
      `}
    >
      {/* 인기 배지 */}
      {isPopular && (
        <div className="absolute -top-4 left-1/2 -translate-x-1/2">
          <span className="bg-blue-500 text-white px-4 py-1 rounded-full text-sm font-semibold">
            인기
          </span>
        </div>
      )}

      {/* 현재 플랜 배지 */}
      {isCurrent && (
        <div className="absolute top-4 right-4">
          <span className="bg-green-500 text-white px-3 py-1 rounded-full text-xs font-semibold">
            현재 플랜
          </span>
        </div>
      )}

      {/* 플랜 이름 */}
      <div className="mb-6">
        <h3 className="text-2xl font-bold text-gray-900">{plan.nameKo}</h3>
        <p className="text-sm text-gray-500 mt-1">{plan.name}</p>
      </div>

      {/* 가격 */}
      <div className="mb-6">
        <div className="flex items-baseline">
          <span className="text-4xl font-bold text-gray-900">
            {plan.price === 0 ? '무료' : formatPrice(plan.price)}
          </span>
          {plan.price > 0 && (
            <span className="text-gray-500 ml-2">/월</span>
          )}
        </div>
      </div>

      {/* 기능 목록 */}
      <ul className="space-y-3 mb-8">
        {plan.featuresKo.map((feature, index) => (
          <li key={index} className="flex items-start">
            <Check className="w-5 h-5 text-green-500 mr-3 flex-shrink-0 mt-0.5" />
            <span className="text-gray-700 text-sm">{feature}</span>
          </li>
        ))}
      </ul>

      {/* 선택 버튼 */}
      <button
        onClick={() => onSelectPlan(plan.id)}
        disabled={loading || isCurrent}
        className={`
          w-full py-3 px-6 rounded-lg font-semibold transition-all
          ${
            isCurrent
              ? 'bg-gray-200 text-gray-500 cursor-not-allowed'
              : isPopular
              ? 'bg-blue-500 text-white hover:bg-blue-600'
              : 'bg-gray-900 text-white hover:bg-gray-800'
          }
          ${loading ? 'opacity-50 cursor-wait' : ''}
        `}
      >
        {isCurrent
          ? '현재 사용 중'
          : plan.price === 0
          ? '무료로 시작하기'
          : '구독하기'}
      </button>
    </div>
  );
};
