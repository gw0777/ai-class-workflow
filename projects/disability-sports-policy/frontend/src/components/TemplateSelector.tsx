import React, { useEffect, useState } from 'react';
import { Layers } from 'lucide-react';
import { getTemplates } from '../api/client';

interface TopicTemplate {
  id: string;
  name: string;
  displayName: string;
  description: string;
  category: string;
}

interface TemplateSelectorProps {
  selectedTopic: string;
  onSelectTopic: (topic: string) => void;
}

export default function TemplateSelector({
  selectedTopic,
  onSelectTopic,
}: TemplateSelectorProps) {
  const [templates, setTemplates] = useState<TopicTemplate[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      const data = await getTemplates();
      setTemplates(data);
    } catch (error) {
      console.error('템플릿 로드 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="animate-pulse space-y-3">
          <div className="h-4 bg-gray-200 rounded w-1/4"></div>
          <div className="h-10 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center mb-4">
        <Layers className="h-5 w-5 text-blue-600 mr-2" />
        <h2 className="text-lg font-semibold text-gray-900">주제 선택</h2>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
        <button
          onClick={() => onSelectTopic('')}
          className={`p-4 rounded-lg border-2 transition-all ${
            selectedTopic === ''
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-200 hover:border-gray-300'
          }`}
        >
          <div className="text-center">
            <div className="text-2xl mb-2">🌐</div>
            <div className="text-sm font-medium text-gray-900">전체</div>
            <div className="text-xs text-gray-500 mt-1">모든 주제</div>
          </div>
        </button>

        {templates.map((template) => (
          <button
            key={template.id}
            onClick={() => onSelectTopic(template.name)}
            className={`p-4 rounded-lg border-2 transition-all ${
              selectedTopic === template.name
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <div className="text-center">
              <div className="text-2xl mb-2">{getCategoryIcon(template.category)}</div>
              <div className="text-sm font-medium text-gray-900">
                {template.displayName}
              </div>
              <div className="text-xs text-gray-500 mt-1 line-clamp-2">
                {template.description}
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}

function getCategoryIcon(category: string): string {
  const icons: Record<string, string> = {
    체육: '⚽',
    교육: '📚',
    보건: '🏥',
    환경: '🌱',
    과학기술: '🔬',
  };
  return icons[category] || '📄';
}
