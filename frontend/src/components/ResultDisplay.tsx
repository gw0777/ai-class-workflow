import React from 'react';
import ReactMarkdown from 'react-markdown';
import { FileText, Clock, DollarSign, Zap } from 'lucide-react';
import { RAGResult } from '../types';

interface ResultDisplayProps {
  result: RAGResult;
}

export default function ResultDisplay({ result }: ResultDisplayProps) {
  const { answer, sources, confidence, metadata } = result;

  return (
    <div className="space-y-6">
      {/* Answer */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">AI 분석 결과</h2>
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-600">신뢰도:</span>
            <div className="flex items-center space-x-1">
              <div className="w-32 h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-green-500"
                  style={{ width: `${confidence * 100}%` }}
                />
              </div>
              <span className="text-sm font-medium text-gray-900">
                {(confidence * 100).toFixed(0)}%
              </span>
            </div>
          </div>
        </div>

        <div className="prose max-w-none">
          <ReactMarkdown>{answer}</ReactMarkdown>
        </div>
      </div>

      {/* Metadata */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          실행 정보
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <MetricCard
            icon={<Zap className="h-5 w-5 text-blue-600" />}
            label="모델"
            value={metadata.model.includes('haiku') ? 'Haiku' : 'Sonnet'}
          />
          <MetricCard
            icon={<Clock className="h-5 w-5 text-green-600" />}
            label="응답 시간"
            value={`${metadata.responseTimeMs}ms`}
          />
          <MetricCard
            icon={<DollarSign className="h-5 w-5 text-yellow-600" />}
            label="비용"
            value={`$${metadata.costUsd.toFixed(6)}`}
          />
          <MetricCard
            icon={<FileText className="h-5 w-5 text-purple-600" />}
            label="토큰"
            value={`${metadata.inputTokens + metadata.outputTokens}`}
          />
        </div>

        <div className="mt-4 pt-4 border-t">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">입력 토큰:</span>
            <span className="font-medium">{metadata.inputTokens}</span>
          </div>
          <div className="flex items-center justify-between text-sm mt-2">
            <span className="text-gray-600">출력 토큰:</span>
            <span className="font-medium">{metadata.outputTokens}</span>
          </div>
          {metadata.cachedTokens > 0 && (
            <div className="flex items-center justify-between text-sm mt-2">
              <span className="text-gray-600">캐시 토큰:</span>
              <span className="font-medium text-green-600">
                {metadata.cachedTokens} (비용 절감!)
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Sources */}
      {sources.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            참고 문서 ({sources.length})
          </h3>
          <div className="space-y-4">
            {sources.map((source, index) => (
              <div
                key={source.chunkId}
                className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-colors"
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-semibold text-blue-600 bg-blue-50 px-2 py-1 rounded">
                        출처 {index + 1}
                      </span>
                      <span className="text-xs text-gray-500">
                        유사도: {(source.score * 100).toFixed(1)}%
                      </span>
                    </div>
                    <h4 className="font-medium text-gray-900 mt-2">
                      {source.title}
                    </h4>
                  </div>
                </div>

                {/* Metadata */}
                <div className="flex flex-wrap gap-2 text-xs text-gray-600 mb-3">
                  {source.metadata.publisher && (
                    <span className="px-2 py-1 bg-gray-100 rounded">
                      {source.metadata.publisher}
                    </span>
                  )}
                  {source.metadata.publishDate && (
                    <span className="px-2 py-1 bg-gray-100 rounded">
                      {new Date(source.metadata.publishDate).toLocaleDateString(
                        'ko-KR'
                      )}
                    </span>
                  )}
                  {source.metadata.documentType && (
                    <span className="px-2 py-1 bg-gray-100 rounded">
                      {source.metadata.documentType}
                    </span>
                  )}
                </div>

                {/* Content Preview */}
                <p className="text-sm text-gray-700 line-clamp-3">
                  {source.content}
                </p>

                {source.metadata.url && (
                  <a
                    href={source.metadata.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-block mt-2 text-xs text-blue-600 hover:text-blue-700"
                  >
                    원문 보기 →
                  </a>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function MetricCard({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-center space-x-3">
      <div className="flex-shrink-0">{icon}</div>
      <div>
        <p className="text-xs text-gray-600">{label}</p>
        <p className="text-sm font-semibold text-gray-900">{value}</p>
      </div>
    </div>
  );
}
