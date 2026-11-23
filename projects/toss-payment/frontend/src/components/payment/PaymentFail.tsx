/**
 * Payment Fail Page
 * 결제 실패 페이지
 */

import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { XCircle, AlertTriangle } from 'lucide-react';
import { tossPaymentService } from '../../services/tossPaymentService';

export const PaymentFail: React.FC = () => {
  const [failInfo, setFailInfo] = useState<{ code: string | null; message: string | null }>({
    code: null,
    message: null,
  });
  const navigate = useNavigate();

  useEffect(() => {
    const info = tossPaymentService.getPaymentFailInfo();
    setFailInfo(info);
  }, []);

  const getFailureReason = (code: string | null): string => {
    const errorMessages: Record<string, string> = {
      'CARD_DECLINED': '카드 승인이 거부되었습니다. 카드사에 문의해주세요.',
      'INSUFFICIENT_BALANCE': '잔액이 부족합니다.',
      'INVALID_CARD_NUMBER': '유효하지 않은 카드 번호입니다.',
      'EXPIRED_CARD': '만료된 카드입니다.',
      'INVALID_CVC': 'CVC 번호가 올바르지 않습니다.',
      'EXCEED_MAX_CARD_QUOTA': '카드 한도를 초과했습니다.',
      'USER_CANCEL': '사용자가 결제를 취소했습니다.',
      'PAYMENT_TIMEOUT': '결제 시간이 초과되었습니다.',
    };

    return errorMessages[code || ''] || failInfo.message || '알 수 없는 오류가 발생했습니다.';
  };

  const handleRetry = () => {
    navigate('/pricing');
  };

  const handleSupport = () => {
    // 고객 지원 페이지로 이동 또는 이메일 열기
    window.location.href = 'mailto:support@airesume.com';
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="bg-white rounded-2xl shadow-lg p-8 max-w-md w-full mx-4">
        <div className="text-center">
          {/* 실패 아이콘 */}
          <XCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />

          {/* 제목 */}
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            결제에 실패했습니다
          </h2>

          {/* 실패 사유 */}
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <div className="flex items-start">
              <AlertTriangle className="w-5 h-5 text-red-500 mr-2 flex-shrink-0 mt-0.5" />
              <div className="text-left">
                <p className="text-sm font-semibold text-red-900 mb-1">
                  실패 사유
                </p>
                <p className="text-sm text-red-700">
                  {getFailureReason(failInfo.code)}
                </p>
                {failInfo.code && (
                  <p className="text-xs text-red-600 mt-2">
                    오류 코드: {failInfo.code}
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* 안내 메시지 */}
          <p className="text-gray-600 mb-6">
            결제가 정상적으로 처리되지 않았습니다. 다시 시도하거나 다른 결제 수단을 이용해주세요.
          </p>

          {/* 액션 버튼들 */}
          <div className="space-y-3">
            <button
              onClick={handleRetry}
              className="w-full bg-blue-500 text-white py-3 rounded-lg font-semibold hover:bg-blue-600 transition-colors"
            >
              다시 시도하기
            </button>

            <button
              onClick={handleSupport}
              className="w-full bg-white text-gray-700 border-2 border-gray-300 py-3 rounded-lg font-semibold hover:bg-gray-50 transition-colors"
            >
              고객 지원 문의
            </button>

            <button
              onClick={() => navigate('/')}
              className="w-full text-gray-500 py-2 hover:text-gray-700 transition-colors"
            >
              홈으로 돌아가기
            </button>
          </div>

          {/* 추가 정보 */}
          <div className="mt-6 pt-6 border-t border-gray-200">
            <p className="text-xs text-gray-500">
              문제가 계속되면 고객센터로 문의해주세요.
              <br />
              support@airesume.com | 1588-0000
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
