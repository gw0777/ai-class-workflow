import React, { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import SearchInterface from './components/SearchInterface';
import TemplateSelector from './components/TemplateSelector';
import PromptGenerator from './components/PromptGenerator';
import ResultDisplay from './components/ResultDisplay';
import { RAGResult } from './types';

const queryClient = new QueryClient();

function App() {
  const [selectedTopic, setSelectedTopic] = useState<string>('');
  const [ragResult, setRagResult] = useState<RAGResult | null>(null);
  const [activeTab, setActiveTab] = useState<'search' | 'prompt'>('search');

  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">
                  범용 정책 분석 플랫폼
                </h1>
                <p className="mt-1 text-sm text-gray-600">
                  6계층 아키텍처 기반 AI 정책 분석 시스템
                </p>
              </div>
              <div className="flex items-center space-x-4">
                <span className="px-3 py-1 bg-green-100 text-green-800 text-sm font-medium rounded-full">
                  ✓ Claude API
                </span>
                <span className="px-3 py-1 bg-blue-100 text-blue-800 text-sm font-medium rounded-full">
                  ✓ RAG
                </span>
              </div>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Topic Selector */}
          <div className="mb-8">
            <TemplateSelector
              selectedTopic={selectedTopic}
              onSelectTopic={setSelectedTopic}
            />
          </div>

          {/* Tabs */}
          <div className="mb-6 border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              <button
                onClick={() => setActiveTab('search')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'search'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                정책 검색 & 분석
              </button>
              <button
                onClick={() => setActiveTab('prompt')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'prompt'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                프롬프트 생성 & 최적화
              </button>
            </nav>
          </div>

          {/* Content */}
          <div className="space-y-8">
            {activeTab === 'search' ? (
              <>
                <SearchInterface
                  selectedTopic={selectedTopic}
                  onResult={setRagResult}
                />
                {ragResult && <ResultDisplay result={ragResult} />}
              </>
            ) : (
              <PromptGenerator selectedTopic={selectedTopic} />
            )}
          </div>
        </main>

        {/* Footer */}
        <footer className="mt-16 bg-white border-t">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div>
                <h3 className="text-sm font-semibold text-gray-900 mb-3">
                  아키텍처
                </h3>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li>• 데이터 수집 (크롤링)</li>
                  <li>• 하이브리드 DB (PostgreSQL + MongoDB + Qdrant)</li>
                  <li>• NLP 처리</li>
                  <li>• Claude API + RAG</li>
                  <li>• Express.js API</li>
                  <li>• React 프론트엔드</li>
                </ul>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-gray-900 mb-3">
                  핵심 기능
                </h3>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li>• 의미 기반 문서 검색</li>
                  <li>• AI 정책 분석</li>
                  <li>• 정책 비교</li>
                  <li>• 트렌드 분석</li>
                  <li>• 프롬프트 최적화</li>
                </ul>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-gray-900 mb-3">
                  지원 주제
                </h3>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li>• 장애인 체육</li>
                  <li>• 교육 정책</li>
                  <li>• 보건의료</li>
                  <li>• 환경 정책</li>
                  <li>• 과학기술</li>
                  <li>• 커스텀 주제 추가 가능</li>
                </ul>
              </div>
            </div>
            <div className="mt-8 pt-8 border-t text-center text-sm text-gray-500">
              © 2024 범용 정책 분석 플랫폼. Powered by Claude API.
            </div>
          </div>
        </footer>
      </div>
    </QueryClientProvider>
  );
}

export default App;
