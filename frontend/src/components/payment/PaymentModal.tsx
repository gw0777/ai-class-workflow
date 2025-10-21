/**
 * Payment Modal Component
 * 결제 모달 컴포넌트
 */

import React, { useState } from 'react';
import { X, CreditCard, Building2 } from 'lucide-react';
import { tossPaymentService } from '../../services/tossPaymentService';
import { subscriptionPlans, PlanType } from '../../config/subscriptionPlans';

interface PaymentModalProps {
  isOpen: boolean;
  onClose: () => void;
  planId: PlanType;
  userId: string;
  userName: string;
  userEmail: string;
}

export const PaymentModal: React.FC<PaymentModalProps> = ({
  isOpen,
  onClose,
  planId,
  userId,
  userName,
  userEmail,
}) => {
  const [paymentMethod, setPaymentMethod] = useState<'card' | 'transfer'>('card');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const plan = subscriptionPlans[planId];

  const handlePayment = async () => {
    setLoading(true);
    setError(null);

    try {
      const paymentRequest = {
        planId,
        userId,
        userName,
        userEmail,
      };

      if (paymentMethod === 'card') {
        await tossPaymentService.requestSubscriptionPayment(paymentRequest);
      } else {
        await tossPaymentService.requestTransferPayment(paymentRequest);
      }
    } catch (err: any) {
      setError(err.message || '결제 요청에 실패했습니다.');
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const formatPrice = (price: number): string => {
    return new Intl.NumberFormat('ko-KR', {
      style: 'currency',
      currency: 'KRW',
    }).format(price);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full mx-4 p-6">
        {/* 헤더 */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-gray-900">결제하기</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
            disabled={loading}
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* 플랜 정보 */}
        <div className="bg-gray-50 rounded-lg p-4 mb-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-gray-600">선택한 플랜</span>
            <span className="font-semibold text-gray-900">{plan.nameKo}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-gray-600">결제 금액</span>
            <span className="text-2xl font-bold text-blue-600">
              {formatPrice(plan.price)}
            </span>
          </div>
        </div>

        {/* 결제 수단 선택 */}
        <div className="mb-6">
          <label className="block text-sm font-semibold text-gray-700 mb-3">
            결제 수단
          </label>
          <div className="grid grid-cols-2 gap-3">
            <button
              onClick={() => setPaymentMethod('card')}
              className={`
                flex items-center justify-center p-4 rounded-lg border-2 transition-all
                ${
                  paymentMethod === 'card'
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 bg-white hover:border-gray-300'
                }
              `}
              disabled={loading}
            >
              <CreditCard className="w-5 h-5 mr-2" />
              <span className="font-medium">카드</span>
            </button>
            <button
              onClick={() => setPaymentMethod('transfer')}
              className={`
                flex items-center justify-center p-4 rounded-lg border-2 transition-all
                ${
                  paymentMethod === 'transfer'
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 bg-white hover:border-gray-300'
                }
              `}
              disabled={loading}
            >
              <Building2 className="w-5 h-5 mr-2" />
              <span className="font-medium">계좌이체</span>
            </button>
          </div>
        </div>

        {/* 에러 메시지 */}
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        {/* 결제 버튼 */}
        <button
          onClick={handlePayment}
          disabled={loading}
          className={`
            w-full py-4 rounded-lg font-semibold text-white transition-all
            ${
              loading
                ? 'bg-gray-400 cursor-wait'
                : 'bg-blue-500 hover:bg-blue-600'
            }
          `}
        >
          {loading ? '결제 진행 중...' : '토스로 결제하기'}
        </button>

        {/* 안내 문구 */}
        <p className="text-xs text-gray-500 text-center mt-4">
          결제는 토스페이먼츠를 통해 안전하게 처리됩니다.
          <br />
          결제 후 즉시 서비스를 이용하실 수 있습니다.
        </p>
      </div>
    </div>
  );
};
