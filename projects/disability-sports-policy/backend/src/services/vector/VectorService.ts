import { QdrantClient } from '@qdrant/js-client-rest';
import axios from 'axios';
import {
  EmbeddingRequest,
  EmbeddingResponse,
  VectorSearchRequest,
  VectorSearchResult,
  RetrievedDocument,
} from '../../models/types';

/**
 * Vector Database 서비스
 * - 임베딩 생성 (다양한 모델 지원)
 * - Qdrant 벡터 검색
 * - 배치 임베딩 처리
 */
export class VectorService {
  private qdrantClient: QdrantClient;
  private collectionName: string;
  private embeddingDimension: number;
  private embeddingModel: string;

  constructor() {
    this.qdrantClient = new QdrantClient({
      url: process.env.QDRANT_URL || 'http://localhost:6333',
      apiKey: process.env.QDRANT_API_KEY,
    });

    this.collectionName =
      process.env.QDRANT_COLLECTION_NAME || 'policy_embeddings';
    this.embeddingDimension = parseInt(
      process.env.EMBEDDING_DIMENSION || '1024'
    );
    this.embeddingModel =
      process.env.EMBEDDING_MODEL || 'multilingual-e5-large';
  }

  /**
   * 임베딩 생성
   *
   * 실제 운영 환경에서는:
   * 1. Hugging Face API (multilingual-e5-large)
   * 2. OpenAI API (text-embedding-3-large)
   * 3. 로컬 모델 서버 (sentence-transformers)
   *
   * 여기서는 간단한 시뮬레이션 임베딩 사용
   */
  async generateEmbedding(text: string): Promise<number[]> {
    try {
      // TODO: 실제 임베딩 API 호출
      // 예시: Hugging Face Inference API
      /*
      const response = await axios.post(
        'https://api-inference.huggingface.co/models/intfloat/multilingual-e5-large',
        { inputs: text },
        {
          headers: {
            'Authorization': `Bearer ${process.env.HUGGINGFACE_API_KEY}`,
          },
        }
      );
      return response.data;
      */

      // 임시: 시뮬레이션 임베딩 (무작위 벡터)
      console.log(
        `[Vector] 임베딩 생성 시뮬레이션: ${text.substring(0, 50)}...`
      );
      return this.generateMockEmbedding(text);
    } catch (error) {
      console.error('[Vector] 임베딩 생성 실패:', error);
      throw error;
    }
  }

  /**
   * 배치 임베딩 생성
   */
  async generateEmbeddings(texts: string[]): Promise<number[][]> {
    const embeddings: number[][] = [];

    // TODO: 실제 배치 API 사용
    for (const text of texts) {
      const embedding = await this.generateEmbedding(text);
      embeddings.push(embedding);
    }

    return embeddings;
  }

  /**
   * 벡터 저장
   */
  async storeVector(
    id: string,
    vector: number[],
    payload: Record<string, any>
  ): Promise<boolean> {
    try {
      await this.qdrantClient.upsert(this.collectionName, {
        wait: true,
        points: [
          {
            id,
            vector,
            payload,
          },
        ],
      });

      console.log(`[Vector] 벡터 저장 완료: ${id}`);
      return true;
    } catch (error) {
      console.error('[Vector] 벡터 저장 실패:', error);
      return false;
    }
  }

  /**
   * 배치 벡터 저장
   */
  async storeBatchVectors(
    points: { id: string; vector: number[]; payload: Record<string, any> }[]
  ): Promise<boolean> {
    try {
      await this.qdrantClient.upsert(this.collectionName, {
        wait: true,
        points,
      });

      console.log(`[Vector] 배치 벡터 저장 완료: ${points.length}개`);
      return true;
    } catch (error) {
      console.error('[Vector] 배치 벡터 저장 실패:', error);
      return false;
    }
  }

  /**
   * 벡터 검색
   */
  async searchSimilar(
    queryVector: number[],
    topK: number = 5,
    filter?: Record<string, any>,
    minScore: number = 0.7
  ): Promise<VectorSearchResult[]> {
    try {
      const searchResult = await this.qdrantClient.search(
        this.collectionName,
        {
          vector: queryVector,
          limit: topK,
          filter: filter,
          with_payload: true,
          score_threshold: minScore,
        }
      );

      return searchResult.map((result) => ({
        id: result.id.toString(),
        score: result.score,
        payload: result.payload || {},
      }));
    } catch (error) {
      console.error('[Vector] 벡터 검색 실패:', error);
      return [];
    }
  }

  /**
   * 텍스트 기반 검색 (임베딩 + 검색)
   */
  async searchByText(
    query: string,
    topK: number = 5,
    filter?: Record<string, any>,
    minScore: number = 0.7
  ): Promise<VectorSearchResult[]> {
    const queryVector = await this.generateEmbedding(query);
    return this.searchSimilar(queryVector, topK, filter, minScore);
  }

  /**
   * 하이브리드 검색 (Vector + Metadata 필터링)
   */
  async hybridSearch(
    query: string,
    filters: {
      topicId?: string;
      documentTypes?: string[];
      publishers?: string[];
      dateRange?: { start?: Date; end?: Date };
    },
    topK: number = 5
  ): Promise<VectorSearchResult[]> {
    // Qdrant 필터 구성
    const qdrantFilter: any = { must: [] };

    if (filters.topicId) {
      qdrantFilter.must.push({
        key: 'topicId',
        match: { value: filters.topicId },
      });
    }

    if (filters.documentTypes && filters.documentTypes.length > 0) {
      qdrantFilter.must.push({
        key: 'documentType',
        match: { any: filters.documentTypes },
      });
    }

    if (filters.publishers && filters.publishers.length > 0) {
      qdrantFilter.must.push({
        key: 'publisher',
        match: { any: filters.publishers },
      });
    }

    if (filters.dateRange) {
      if (filters.dateRange.start) {
        qdrantFilter.must.push({
          key: 'publishDate',
          range: {
            gte: filters.dateRange.start.toISOString(),
          },
        });
      }
      if (filters.dateRange.end) {
        qdrantFilter.must.push({
          key: 'publishDate',
          range: {
            lte: filters.dateRange.end.toISOString(),
          },
        });
      }
    }

    const queryVector = await this.generateEmbedding(query);
    return this.searchSimilar(
      queryVector,
      topK,
      qdrantFilter.must.length > 0 ? qdrantFilter : undefined
    );
  }

  /**
   * 벡터 삭제
   */
  async deleteVector(id: string): Promise<boolean> {
    try {
      await this.qdrantClient.delete(this.collectionName, {
        wait: true,
        points: [id],
      });

      console.log(`[Vector] 벡터 삭제 완료: ${id}`);
      return true;
    } catch (error) {
      console.error('[Vector] 벡터 삭제 실패:', error);
      return false;
    }
  }

  /**
   * 컬렉션 정보 조회
   */
  async getCollectionInfo(): Promise<any> {
    try {
      return await this.qdrantClient.getCollection(this.collectionName);
    } catch (error) {
      console.error('[Vector] 컬렉션 정보 조회 실패:', error);
      return null;
    }
  }

  /**
   * 시뮬레이션 임베딩 생성 (개발/테스트용)
   * 실제 운영 환경에서는 제거하고 실제 API 사용
   */
  private generateMockEmbedding(text: string): number[] {
    // 텍스트 기반 시드로 일관된 "무작위" 벡터 생성
    const seed = this.hashString(text);
    const random = this.seededRandom(seed);

    const embedding: number[] = [];
    for (let i = 0; i < this.embeddingDimension; i++) {
      embedding.push(random() * 2 - 1); // -1 ~ 1 범위
    }

    // 정규화 (L2 norm = 1)
    const norm = Math.sqrt(
      embedding.reduce((sum, val) => sum + val * val, 0)
    );
    return embedding.map((val) => val / norm);
  }

  /**
   * 문자열 해싱
   */
  private hashString(str: string): number {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = (hash << 5) - hash + char;
      hash = hash & hash;
    }
    return Math.abs(hash);
  }

  /**
   * 시드 기반 무작위 생성
   */
  private seededRandom(seed: number): () => number {
    let s = seed;
    return () => {
      s = (s * 9301 + 49297) % 233280;
      return s / 233280;
    };
  }
}

/**
 * 문서 임베딩 서비스
 * - 문서를 청크로 분할하고 임베딩 생성
 * - PostgreSQL + Vector DB에 저장
 */
export class DocumentEmbeddingService {
  private vectorService: VectorService;

  constructor(vectorService: VectorService) {
    this.vectorService = vectorService;
  }

  /**
   * 문서 임베딩 및 저장
   */
  async embedDocument(
    documentId: string,
    chunks: { id: string; content: string; metadata: Record<string, any> }[]
  ): Promise<boolean> {
    try {
      console.log(
        `[Embedding] 문서 임베딩 시작: ${documentId} (${chunks.length} chunks)`
      );

      const points: {
        id: string;
        vector: number[];
        payload: Record<string, any>;
      }[] = [];

      for (const chunk of chunks) {
        const vector = await this.vectorService.generateEmbedding(
          chunk.content
        );

        points.push({
          id: chunk.id,
          vector,
          payload: {
            documentId,
            content: chunk.content,
            ...chunk.metadata,
          },
        });
      }

      // 배치 저장
      const success = await this.vectorService.storeBatchVectors(points);

      if (success) {
        console.log(`[Embedding] 문서 임베딩 완료: ${documentId}`);
      }

      return success;
    } catch (error) {
      console.error(`[Embedding] 문서 임베딩 실패: ${documentId}`, error);
      return false;
    }
  }

  /**
   * RAG 검색 (벡터 검색 + 문서 정보 결합)
   */
  async searchForRAG(
    query: string,
    topK: number = 5,
    filters?: Record<string, any>
  ): Promise<RetrievedDocument[]> {
    const vectorResults = await this.vectorService.searchByText(
      query,
      topK,
      filters
    );

    return vectorResults.map((result) => ({
      documentId: result.payload.documentId as string,
      chunkId: result.id,
      title: result.payload.title as string,
      content: result.payload.content as string,
      score: result.score,
      metadata: {
        publisher: result.payload.publisher as string | undefined,
        publishDate: result.payload.publishDate
          ? new Date(result.payload.publishDate as string)
          : undefined,
        documentType: result.payload.documentType as string | undefined,
        url: result.payload.url as string | undefined,
      },
    }));
  }
}
