/**
 * AI Resume Master Subscription Plans
 * 구독 플랜 정의
 */

export type PlanType = 'free' | 'starter' | 'pro';

export interface SubscriptionPlan {
  id: PlanType;
  name: string;
  nameKo: string;
  price: number;
  billingCycle: 'monthly' | 'yearly';
  features: string[];
  featuresKo: string[];
  limits: {
    atsAnalysis: number | 'unlimited';
    templates: number | 'unlimited';
    aiPhotoAnalysis: boolean;
    voiceInterview: boolean;
    consulting: boolean;
    keywordOptimization: boolean;
  };
  popular?: boolean;
}

export const subscriptionPlans: Record<PlanType, SubscriptionPlan> = {
  free: {
    id: 'free',
    name: 'Free',
    nameKo: '무료',
    price: 0,
    billingCycle: 'monthly',
    features: [
      '3 ATS analyses per month',
      '1 basic template',
      'Basic keyword suggestions',
    ],
    featuresKo: [
      '월 3회 ATS 분석',
      '기본 템플릿 1종',
      '기본 키워드 제안',
    ],
    limits: {
      atsAnalysis: 3,
      templates: 1,
      aiPhotoAnalysis: false,
      voiceInterview: false,
      consulting: false,
      keywordOptimization: false,
    },
  },

  starter: {
    id: 'starter',
    name: 'Starter',
    nameKo: '스타터',
    price: 9900,
    billingCycle: 'monthly',
    features: [
      'Unlimited ATS analysis',
      '5 premium templates',
      'Advanced keyword optimization',
      'Email support',
    ],
    featuresKo: [
      '무제한 ATS 분석',
      '프리미엄 템플릿 5종',
      '고급 키워드 최적화',
      '이메일 지원',
    ],
    limits: {
      atsAnalysis: 'unlimited',
      templates: 5,
      aiPhotoAnalysis: false,
      voiceInterview: false,
      consulting: false,
      keywordOptimization: true,
    },
    popular: true,
  },

  pro: {
    id: 'pro',
    name: 'Pro',
    nameKo: '프로',
    price: 29900,
    billingCycle: 'monthly',
    features: [
      'All Starter features',
      'Unlimited templates',
      'AI photo analysis',
      'Voice interview preparation',
      '1:1 career consulting',
      'Priority support',
    ],
    featuresKo: [
      '스타터 플랜 전체 기능',
      '무제한 템플릿',
      'AI 사진 분석',
      '음성 인터뷰 준비',
      '1:1 커리어 컨설팅',
      '우선 지원',
    ],
    limits: {
      atsAnalysis: 'unlimited',
      templates: 'unlimited',
      aiPhotoAnalysis: true,
      voiceInterview: true,
      consulting: true,
      keywordOptimization: true,
    },
  },
};

/**
 * 플랜별 가격 정보 가져오기
 */
export const getPlanPrice = (planId: PlanType): number => {
  return subscriptionPlans[planId].price;
};

/**
 * 플랜 기능 비교
 */
export const comparePlans = (
  currentPlan: PlanType,
  targetPlan: PlanType
): 'upgrade' | 'downgrade' | 'same' => {
  const planOrder: Record<PlanType, number> = { free: 0, starter: 1, pro: 2 };
  const currentOrder = planOrder[currentPlan];
  const targetOrder = planOrder[targetPlan];

  if (currentOrder < targetOrder) return 'upgrade';
  if (currentOrder > targetOrder) return 'downgrade';
  return 'same';
};

/**
 * 플랜 혜택 확인
 */
export const hasFeature = (
  planId: PlanType,
  feature: keyof SubscriptionPlan['limits']
): boolean => {
  const limit = subscriptionPlans[planId].limits[feature];
  return limit === 'unlimited' || limit === true || (typeof limit === 'number' && limit > 0);
};
