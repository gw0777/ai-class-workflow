import React, { useState } from 'react';
import { Search, Loader2, Sparkles } from 'lucide-react';
import { ragQuery } from '../api/client';
import { RAGResult } from '../types';

interface SearchInterfaceProps {
  selectedTopic: string;
  onResult: (result: RAGResult) => void;
}

export default function SearchInterface({ selectedTopic, onResult }: SearchInterfaceProps) {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [model, setModel] = useState<'haiku' | 'sonnet'>('sonnet');
  const [topK, setTopK] = useState(5);
  const [useCache, setUseCache] = useState(true);

  const handleSearch = async () => {
    if (!query.trim()) return;

    setLoading(true);
    try {
      const result = await ragQuery({
        query,
        topicName: selectedTopic || undefined,
        topK,
        model,
        useCache,
      });

      onResult(result);
    } catch (error) {
      console.error('검색 실패:', error);
      alert('검색에 실패했습니다. 다시 시도해주세요.');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSearch();
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-2">
          정책 검색 & AI 분석
        </h2>
        <p className="text-sm text-gray-600">
          질문을 입력하면 관련 정책 문서를 검색하고 AI가 분석 결과를 제공합니다.
        </p>
      </div>

      {/* Search Input */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          질문
        </label>
        <div className="relative">
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="예: 2024년 장애인 생활체육 참여율은 얼마나 되나요?"
            className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            rows={3}
          />
          <Search className="absolute right-3 top-3 h-5 w-5 text-gray-400" />
        </div>
      </div>

      {/* Options */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        {/* Model Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            모델 선택
          </label>
          <select
            value={model}
            onChange={(e) => setModel(e.target.value as 'haiku' | 'sonnet')}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="haiku">Claude 3 Haiku (빠름, 저렴)</option>
            <option value="sonnet">Claude 3.5 Sonnet (정확, 추천)</option>
          </select>
        </div>

        {/* Top K */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            검색 문서 수
          </label>
          <input
            type="number"
            value={topK}
            onChange={(e) => setTopK(Number(e.target.value))}
            min={1}
            max={10}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Caching */}
        <div className="flex items-center pt-6">
          <input
            type="checkbox"
            id="useCache"
            checked={useCache}
            onChange={(e) => setUseCache(e.target.checked)}
            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          />
          <label htmlFor="useCache" className="ml-2 text-sm text-gray-700">
            Prompt Caching 사용 (비용 절감)
          </label>
        </div>
      </div>

      {/* Search Button */}
      <button
        onClick={handleSearch}
        disabled={loading || !query.trim()}
        className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center space-x-2 transition-colors"
      >
        {loading ? (
          <>
            <Loader2 className="h-5 w-5 animate-spin" />
            <span>분석 중...</span>
          </>
        ) : (
          <>
            <Sparkles className="h-5 w-5" />
            <span>AI 분석 시작</span>
          </>
        )}
      </button>

      {/* Examples */}
      <div className="mt-6 pt-6 border-t">
        <p className="text-sm font-medium text-gray-700 mb-3">예시 질문:</p>
        <div className="space-y-2">
          {[
            '2024년 장애인 생활체육 참여율은?',
            '반다비 체육센터 건립 현황은?',
            '장애인체육 예산은 전년 대비 얼마나 증가했나?',
            'IPC 접근성 가이드라인의 주요 내용은?',
          ].map((example, index) => (
            <button
              key={index}
              onClick={() => setQuery(example)}
              className="block w-full text-left px-3 py-2 text-sm text-gray-600 hover:bg-gray-50 rounded-lg transition-colors"
            >
              • {example}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
