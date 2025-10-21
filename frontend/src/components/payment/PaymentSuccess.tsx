/**
 * Payment Success Page
 * 결제 성공 페이지
 */

import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckCircle, Loader } from 'lucide-react';
import { tossPaymentService } from '../../services/tossPaymentService';
import { getFunctions, httpsCallable } from 'firebase/functions';

export const PaymentSuccess: React.FC = () => {
  const [processing, setProcessing] = useState(true);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    confirmPayment();
  }, []);

  const confirmPayment = async () => {
    try {
      // URL에서 결제 정보 추출
      const { paymentKey, orderId, amount } = tossPaymentService.getPaymentInfoFromUrl();

      if (!paymentKey || !orderId || !amount) {
        throw new Error('결제 정보가 없습니다.');
      }

      // Cloud Function 호출하여 결제 승인
      const functions = getFunctions();
      const confirmTossPayment = httpsCallable(functions, 'confirmTossPayment');

      const result = await confirmTossPayment({
        paymentKey,
        orderId,
        amount: parseInt(amount),
        userId: 'USER_ID_HERE', // 실제 사용자 ID로 교체
        planId: 'PLAN_ID_HERE', // 실제 플랜 ID로 교체
      });

      const response = result.data as any;

      if (response.success) {
        setSuccess(true);
        // 3초 후 대시보드로 이동
        setTimeout(() => {
          navigate('/dashboard');
        }, 3000);
      } else {
        throw new Error(response.error || '결제 승인에 실패했습니다.');
      }
    } catch (err: any) {
      console.error('결제 승인 실패:', err);
      setError(err.message || '결제 처리 중 오류가 발생했습니다.');
    } finally {
      setProcessing(false);
    }
  };

  if (processing) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <Loader className="w-16 h-16 text-blue-500 animate-spin mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            결제를 처리하고 있습니다
          </h2>
          <p className="text-gray-600">잠시만 기다려주세요...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="bg-white rounded-2xl shadow-lg p-8 max-w-md w-full mx-4">
          <div className="text-center">
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-red-500 text-4xl">×</span>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              결제 처리 실패
            </h2>
            <p className="text-gray-600 mb-6">{error}</p>
            <button
              onClick={() => navigate('/pricing')}
              className="w-full bg-blue-500 text-white py-3 rounded-lg font-semibold hover:bg-blue-600 transition-colors"
            >
              다시 시도하기
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="bg-white rounded-2xl shadow-lg p-8 max-w-md w-full mx-4">
        <div className="text-center">
          <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            결제가 완료되었습니다!
          </h2>
          <p className="text-gray-600 mb-6">
            구독이 활성화되었습니다. 이제 모든 기능을 사용하실 수 있습니다.
          </p>
          <div className="bg-blue-50 rounded-lg p-4 mb-6">
            <p className="text-sm text-blue-800">
              곧 대시보드로 이동합니다...
            </p>
          </div>
          <button
            onClick={() => navigate('/dashboard')}
            className="w-full bg-blue-500 text-white py-3 rounded-lg font-semibold hover:bg-blue-600 transition-colors"
          >
            대시보드로 이동
          </button>
        </div>
      </div>
    </div>
  );
};
