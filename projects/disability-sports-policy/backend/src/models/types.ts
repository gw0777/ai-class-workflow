/**
 * 범용 정책 분석 플랫폼 - TypeScript 타입 정의
 */

// ============================================================================
// 주제 템플릿 (Topic Template)
// ============================================================================
export interface TopicTemplate {
  id: string;
  name: string;
  displayName: string;
  description?: string;
  category?: string;
  config: TopicConfig;
  isActive: boolean;
  createdAt: Date;
  updatedAt: Date;
}

export interface TopicConfig {
  keywords: string[];
  sources: SourceConfig[];
  documentTypes: string[];
  nlpConfig: NLPConfig;
  crawlerConfig: CrawlerConfig;
}

export interface SourceConfig {
  name: string;
  type: 'government' | 'organization' | 'academic' | 'international' | 'local';
  url?: string;
  apiEndpoint?: string;
}

export interface NLPConfig {
  language: string;
  domainDict?: string;
  entities: string[];
  stopwords?: string[];
}

export interface CrawlerConfig {
  urls: string[];
  selectors?: Record<string, string>;
  pagination?: {
    type: 'page' | 'infinite_scroll';
    selector: string;
  };
  rateLimit?: number;
}

// ============================================================================
// 문서 소스 (Document Source)
// ============================================================================
export interface DocumentSource {
  id: string;
  topicId: string;
  name: string;
  sourceType: 'government' | 'academic' | 'international' | 'local';
  url?: string;
  apiEndpoint?: string;
  crawlerConfig?: Record<string, any>;
  lastCrawledAt?: Date;
  crawlFrequencyHours: number;
  isActive: boolean;
  createdAt: Date;
  updatedAt: Date;
}

// ============================================================================
// 정책 문서 (Policy Document)
// ============================================================================
export interface PolicyDocument {
  id: string;
  topicId?: string;
  sourceId?: string;
  title: string;
  titleEn?: string;
  documentType?: string;
  publisher?: string;
  author?: string;
  publishDate?: Date;
  category?: string;
  subcategory?: string;
  tags?: string[];
  keywords?: string[];
  url?: string;
  filePath?: string;
  mongodbId?: string;
  processingStatus: 'pending' | 'processing' | 'completed' | 'failed';
  isEmbedded: boolean;
  pageCount?: number;
  wordCount?: number;
  language: string;
  metadata?: Record<string, any>;
  createdAt: Date;
  updatedAt: Date;
}

// ============================================================================
// 문서 청크 (Document Chunk)
// ============================================================================
export interface DocumentChunk {
  id: string;
  documentId: string;
  chunkIndex: number;
  content: string;
  vectorId?: string;
  embeddingModel: string;
  startPosition?: number;
  endPosition?: number;
  pageNumber?: number;
  metadata?: Record<string, any>;
  createdAt: Date;
}

// ============================================================================
// 분석 작업 (Analysis Job)
// ============================================================================
export interface AnalysisJob {
  id: string;
  topicId?: string;
  jobType: 'rag_query' | 'comparison' | 'trend_analysis' | 'entity_extraction';
  query?: string;
  config?: Record<string, any>;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  result?: Record<string, any>;
  errorMessage?: string;
  claudeModel?: string;
  inputTokens?: number;
  outputTokens?: number;
  cachedTokens?: number;
  costUsd?: number;
  startedAt?: Date;
  completedAt?: Date;
  durationMs?: number;
  createdAt: Date;
}

// ============================================================================
// 프롬프트 템플릿 (Prompt Template)
// ============================================================================
export interface PromptTemplate {
  id: string;
  topicId: string;
  name: string;
  description?: string;
  systemPrompt: string;
  userPromptTemplate: string;
  model: string;
  maxTokens: number;
  temperature: number;
  enableCaching: boolean;
  cacheTtlMinutes: number;
  usageCount: number;
  avgInputTokens?: number;
  avgOutputTokens?: number;
  avgResponseTimeMs?: number;
  isActive: boolean;
  createdAt: Date;
  updatedAt: Date;
}

// ============================================================================
// Named Entity
// ============================================================================
export interface NamedEntity {
  id: string;
  documentId: string;
  entityType: 'organization' | 'law' | 'program' | 'budget' | 'date' | 'person' | 'location';
  entityText: string;
  normalizedText?: string;
  context?: string;
  frequency: number;
  confidence?: number;
  metadata?: Record<string, any>;
  createdAt: Date;
}

// ============================================================================
// RAG 관련 타입
// ============================================================================
export interface RAGQuery {
  query: string;
  topicId?: string;
  filters?: DocumentFilter;
  topK?: number;
  minScore?: number;
  model?: 'haiku' | 'sonnet';
  enableCaching?: boolean;
}

export interface DocumentFilter {
  documentTypes?: string[];
  publishers?: string[];
  dateRange?: {
    start?: Date;
    end?: Date;
  };
  categories?: string[];
  tags?: string[];
  language?: string;
}

export interface RAGResult {
  answer: string;
  sources: RetrievedDocument[];
  confidence: number;
  metadata: {
    model: string;
    inputTokens: number;
    outputTokens: number;
    cachedTokens: number;
    responseTimeMs: number;
    costUsd: number;
  };
}

export interface RetrievedDocument {
  documentId: string;
  chunkId: string;
  title: string;
  content: string;
  score: number;
  metadata: {
    publisher?: string;
    publishDate?: Date;
    documentType?: string;
    url?: string;
  };
}

// ============================================================================
// Embedding 관련 타입
// ============================================================================
export interface EmbeddingRequest {
  text: string;
  model?: string;
}

export interface EmbeddingResponse {
  embedding: number[];
  model: string;
  dimensions: number;
}

export interface VectorSearchRequest {
  query: string;
  topK: number;
  filter?: Record<string, any>;
  minScore?: number;
}

export interface VectorSearchResult {
  id: string;
  score: number;
  payload: Record<string, any>;
}

// ============================================================================
// 크롤링 관련 타입
// ============================================================================
export interface CrawlJob {
  sourceId: string;
  url: string;
  depth?: number;
  maxPages?: number;
}

export interface CrawlResult {
  url: string;
  title: string;
  content: string;
  metadata: {
    publishDate?: Date;
    author?: string;
    tags?: string[];
  };
  links: string[];
  success: boolean;
  error?: string;
}

// ============================================================================
// NLP 처리 관련 타입
// ============================================================================
export interface NLPProcessingResult {
  tokens: string[];
  entities: NamedEntity[];
  keywords: string[];
  summary?: string;
  topics?: string[];
  sentiment?: {
    score: number;
    label: 'positive' | 'negative' | 'neutral';
  };
}

// ============================================================================
// 사용자 관련 타입 (선택적)
// ============================================================================
export interface User {
  id: string;
  email: string;
  name?: string;
  role: 'admin' | 'user' | 'guest';
  isActive: boolean;
  createdAt: Date;
  updatedAt: Date;
}

export interface UserSession {
  id: string;
  userId: string;
  token: string;
  expiresAt: Date;
  createdAt: Date;
}

// ============================================================================
// API 응답 타입
// ============================================================================
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
  metadata?: {
    page?: number;
    limit?: number;
    total?: number;
    timestamp: string;
  };
}

export interface PaginationParams {
  page: number;
  limit: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

// ============================================================================
// 통계 타입
// ============================================================================
export interface TopicStatistics {
  topicId: string;
  topicName: string;
  totalDocuments: number;
  embeddedDocuments: number;
  uniquePublishers: number;
  earliestDate?: Date;
  latestDate?: Date;
  totalWords: number;
}

export interface AnalysisStatistics {
  totalJobs: number;
  completedJobs: number;
  failedJobs: number;
  avgResponseTimeMs: number;
  totalCostUsd: number;
  tokenUsage: {
    input: number;
    output: number;
    cached: number;
  };
}
