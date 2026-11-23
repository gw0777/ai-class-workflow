import axios from 'axios';
import { RAGResult } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ============================================================================
// Templates API
// ============================================================================
export async function getTemplates() {
  const response = await apiClient.get('/templates');
  return response.data.data;
}

export async function getTemplate(name: string) {
  const response = await apiClient.get(`/templates/${name}`);
  return response.data.data;
}

export async function createTemplate(data: {
  name: string;
  displayName: string;
  description: string;
  category: string;
}) {
  const response = await apiClient.post('/templates/create', data);
  return response.data.data;
}

// ============================================================================
// RAG API
// ============================================================================
export async function ragQuery(data: {
  query: string;
  topicName?: string;
  topK?: number;
  minScore?: number;
  model?: 'haiku' | 'sonnet';
  useCache?: boolean;
}): Promise<RAGResult> {
  const response = await apiClient.post('/rag/query', data);
  return response.data.data;
}

export async function vectorSearch(data: {
  query: string;
  topK?: number;
  filters?: any;
}) {
  const response = await apiClient.post('/rag/search', data);
  return response.data.data;
}

export async function comparePolicies(data: {
  policies: { title: string; content: string }[];
  criteria?: string[];
}) {
  const response = await apiClient.post('/rag/compare', data);
  return response.data.data;
}

export async function analyzeTrend(data: {
  documents: { date: Date; title: string; summary: string }[];
}) {
  const response = await apiClient.post('/rag/trend', data);
  return response.data.data;
}

// ============================================================================
// Prompt Optimization API
// ============================================================================
export async function evaluatePrompt(prompt: string) {
  const response = await apiClient.post('/rag/prompt/evaluate', { prompt });
  return response.data.data;
}

export async function improvePrompt(prompt: string) {
  const response = await apiClient.post('/rag/prompt/improve', { prompt });
  return response.data.data;
}

// ============================================================================
// Documents API
// ============================================================================
export async function getDocuments(params?: {
  page?: number;
  limit?: number;
  topicId?: string;
  documentType?: string;
  publisher?: string;
}) {
  const response = await apiClient.get('/documents', { params });
  return response.data.data;
}

export async function getDocument(id: string) {
  const response = await apiClient.get(`/documents/${id}`);
  return response.data.data;
}

export async function uploadDocument(data: {
  topicId?: string;
  title: string;
  content: string;
  metadata?: any;
}) {
  const response = await apiClient.post('/documents/upload', data);
  return response.data.data;
}

// ============================================================================
// Analysis API
// ============================================================================
export async function getAnalysisJobs(params?: {
  page?: number;
  limit?: number;
  status?: string;
  jobType?: string;
}) {
  const response = await apiClient.get('/analysis/jobs', { params });
  return response.data.data;
}

export async function getAnalysisJob(id: string) {
  const response = await apiClient.get(`/analysis/jobs/${id}`);
  return response.data.data;
}

export async function getAnalysisStatistics() {
  const response = await apiClient.get('/analysis/statistics');
  return response.data.data;
}

export default apiClient;
