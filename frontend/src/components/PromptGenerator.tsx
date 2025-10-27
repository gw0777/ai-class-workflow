import React, { useState } from 'react';
import { Wand2, Copy, CheckCircle, RefreshCw } from 'lucide-react';
import { evaluatePrompt, improvePrompt } from '../api/client';

interface PromptGeneratorProps {
  selectedTopic: string;
}

export default function PromptGenerator({ selectedTopic }: PromptGeneratorProps) {
  const [prompt, setPrompt] = useState('');
  const [evaluation, setEvaluation] = useState<any>(null);
  const [improvedPrompt, setImprovedPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleEvaluate = async () => {
    if (!prompt.trim()) return;

    setLoading(true);
    try {
      const result = await evaluatePrompt(prompt);
      setEvaluation(result);
    } catch (error) {
      console.error('평가 실패:', error);
      alert('프롬프트 평가에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleImprove = async () => {
    if (!prompt.trim()) return;

    setLoading(true);
    try {
      const result = await improvePrompt(prompt);
      setImprovedPrompt(result.improved);
    } catch (error) {
      console.error('개선 실패:', error);
      alert('프롬프트 개선에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Input */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          프롬프트 생성 & 최적화
        </h2>
        <p className="text-sm text-gray-600 mb-4">
          프롬프트를 입력하면 AI가 품질을 평가하고 개선 방안을 제안합니다.
        </p>

        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="프롬프트를 입력하세요..."
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
          rows={8}
        />

        <div className="flex space-x-3 mt-4">
          <button
            onClick={handleEvaluate}
            disabled={loading || !prompt.trim()}
            className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
          >
            <CheckCircle className="h-5 w-5" />
            <span>평가하기</span>
          </button>
          <button
            onClick={handleImprove}
            disabled={loading || !prompt.trim()}
            className="flex-1 px-4 py-2 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
          >
            <Wand2 className="h-5 w-5" />
            <span>개선하기</span>
          </button>
        </div>
      </div>

      {/* Evaluation Result */}
      {evaluation && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            평가 결과
          </h3>

          {/* Score */}
          <div className="mb-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">
                품질 점수
              </span>
              <span className="text-2xl font-bold text-blue-600">
                {evaluation.score}/100
              </span>
            </div>
            <div className="w-full h-3 bg-gray-200 rounded-full overflow-hidden">
              <div
                className={`h-full ${
                  evaluation.score >= 80
                    ? 'bg-green-500'
                    : evaluation.score >= 60
                    ? 'bg-yellow-500'
                    : 'bg-red-500'
                }`}
                style={{ width: `${evaluation.score}%` }}
              />
            </div>
          </div>

          {/* Feedback */}
          <div className="mb-6">
            <h4 className="text-sm font-semibold text-gray-900 mb-2">
              종합 평가
            </h4>
            <p className="text-sm text-gray-700">{evaluation.feedback}</p>
          </div>

          {/* Suggestions */}
          {evaluation.suggestions && evaluation.suggestions.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-gray-900 mb-2">
                개선 제안
              </h4>
              <ul className="space-y-2">
                {evaluation.suggestions.map((suggestion: string, index: number) => (
                  <li
                    key={index}
                    className="flex items-start text-sm text-gray-700"
                  >
                    <span className="text-blue-600 mr-2">•</span>
                    <span>{suggestion}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Improved Prompt */}
      {improvedPrompt && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">
              개선된 프롬프트
            </h3>
            <button
              onClick={() => handleCopy(improvedPrompt)}
              className="px-3 py-1 text-sm text-blue-600 hover:text-blue-700 flex items-center space-x-1"
            >
              {copied ? (
                <>
                  <CheckCircle className="h-4 w-4" />
                  <span>복사됨!</span>
                </>
              ) : (
                <>
                  <Copy className="h-4 w-4" />
                  <span>복사</span>
                </>
              )}
            </button>
          </div>

          <div className="bg-gray-50 rounded-lg p-4">
            <pre className="whitespace-pre-wrap text-sm text-gray-800">
              {improvedPrompt}
            </pre>
          </div>

          <button
            onClick={() => setPrompt(improvedPrompt)}
            className="mt-4 w-full px-4 py-2 border border-blue-600 text-blue-600 rounded-lg font-medium hover:bg-blue-50 flex items-center justify-center space-x-2"
          >
            <RefreshCw className="h-4 w-4" />
            <span>이 프롬프트로 다시 평가하기</span>
          </button>
        </div>
      )}

      {/* Templates */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          프롬프트 템플릿
        </h3>
        <div className="space-y-3">
          {PROMPT_TEMPLATES.map((template, index) => (
            <button
              key={index}
              onClick={() => setPrompt(template.prompt)}
              className="w-full text-left px-4 py-3 border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-all"
            >
              <div className="font-medium text-gray-900 mb-1">
                {template.name}
              </div>
              <div className="text-sm text-gray-600">{template.description}</div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

const PROMPT_TEMPLATES = [
  {
    name: '정책 요약',
    description: '정책 문서를 체계적으로 요약합니다.',
    prompt: `다음 정책 문서를 요약해주세요:

{content}

**요약 항목:**
1. 정책 목표
2. 주요 내용
3. 대상 및 범위
4. 예산 및 기간
5. 기대 효과

각 항목을 명확하고 간결하게 정리해주세요.`,
  },
  {
    name: '정책 비교',
    description: '여러 정책을 비교 분석합니다.',
    prompt: `다음 정책들을 비교 분석해주세요:

**정책 A:**
{policy_a}

**정책 B:**
{policy_b}

**비교 기준:**
1. 목적 및 배경
2. 주요 내용 차이점
3. 예산 및 규모
4. 대상 및 적용 범위
5. 장단점

표 형식으로 비교하고, 종합 의견을 제시해주세요.`,
  },
  {
    name: '트렌드 분석',
    description: '시계열 정책 변화를 분석합니다.',
    prompt: `다음은 연도별 정책 문서입니다:

{documents}

**분석 요청:**
1. 주요 정책 변화의 흐름
2. 새롭게 등장한 주제나 키워드
3. 강화되거나 약화된 정책 방향
4. 향후 예상되는 정책 방향

시계열 관점에서 분석해주세요.`,
  },
];
