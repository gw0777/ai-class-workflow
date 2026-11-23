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

export interface TopicTemplate {
  id: string;
  name: string;
  displayName: string;
  description: string;
  category: string;
  config: {
    keywords: string[];
    sources: any[];
    documentTypes: string[];
    nlpConfig: any;
    crawlerConfig: any;
  };
  isActive: boolean;
  createdAt: Date;
  updatedAt: Date;
}

export interface PolicyDocument {
  id: string;
  title: string;
  documentType?: string;
  publisher?: string;
  publishDate?: Date;
  category?: string;
  tags?: string[];
  keywords?: string[];
  url?: string;
  content?: string;
}
