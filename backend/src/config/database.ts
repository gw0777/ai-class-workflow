import { Pool } from 'pg';
import { MongoClient, Db } from 'mongodb';
import { QdrantClient } from '@qdrant/js-client-rest';
import dotenv from 'dotenv';

dotenv.config();

/**
 * PostgreSQL 연결 풀 (구조화 메타데이터 관리)
 * - 정책 문서의 메타데이터 (제목, 발행기관, 날짜, 카테고리)
 * - ACID 트랜잭션 지원
 * - 복잡한 조인 및 집계 쿼리
 */
export const pgPool = new Pool({
  host: process.env.POSTGRES_HOST || 'localhost',
  port: parseInt(process.env.POSTGRES_PORT || '5432'),
  database: process.env.POSTGRES_DB || 'policy_analysis',
  user: process.env.POSTGRES_USER || 'postgres',
  password: process.env.POSTGRES_PASSWORD,
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

/**
 * MongoDB 클라이언트 (비구조화 문서 원문 저장)
 * - 정책 문서 전체 텍스트 JSON 저장
 * - 스키마리스 구조로 유연한 필드 관리
 * - 샤딩을 통한 수평 확장
 */
let mongoDb: Db | null = null;
const mongoClient = new MongoClient(
  process.env.MONGODB_URI || 'mongodb://localhost:27017'
);

export const connectMongoDB = async (): Promise<Db> => {
  if (!mongoDb) {
    await mongoClient.connect();
    mongoDb = mongoClient.db(process.env.MONGODB_DB_NAME || 'policy_documents');
    console.log('✅ MongoDB 연결 성공');
  }
  return mongoDb;
};

export const getMongoDb = (): Db => {
  if (!mongoDb) {
    throw new Error('MongoDB가 연결되지 않았습니다. connectMongoDB()를 먼저 호출하세요.');
  }
  return mongoDb;
};

/**
 * Qdrant Vector Database 클라이언트 (의미 기반 검색)
 * - 문서 임베딩 벡터 저장
 * - HNSW 인덱스로 빠른 유사도 검색
 * - 코사인 유사도 기반 검색
 */
export const qdrantClient = new QdrantClient({
  url: process.env.QDRANT_URL || 'http://localhost:6333',
  apiKey: process.env.QDRANT_API_KEY,
});

/**
 * 데이터베이스 초기화
 */
export const initializeDatabases = async () => {
  try {
    // PostgreSQL 연결 테스트
    const pgClient = await pgPool.connect();
    console.log('✅ PostgreSQL 연결 성공');
    pgClient.release();

    // MongoDB 연결
    await connectMongoDB();

    // Qdrant 연결 테스트
    const collections = await qdrantClient.getCollections();
    console.log('✅ Qdrant 연결 성공');

    // Qdrant 컬렉션 생성 (없는 경우)
    const collectionName = process.env.QDRANT_COLLECTION_NAME || 'policy_embeddings';
    const collectionExists = collections.collections.some(
      (col) => col.name === collectionName
    );

    if (!collectionExists) {
      await qdrantClient.createCollection(collectionName, {
        vectors: {
          size: parseInt(process.env.EMBEDDING_DIMENSION || '1024'),
          distance: 'Cosine',
        },
      });
      console.log(`✅ Qdrant 컬렉션 '${collectionName}' 생성 완료`);
    }

    console.log('🎉 모든 데이터베이스 초기화 완료');
  } catch (error) {
    console.error('❌ 데이터베이스 초기화 실패:', error);
    throw error;
  }
};

/**
 * 데이터베이스 연결 종료
 */
export const closeDatabases = async () => {
  await pgPool.end();
  await mongoClient.close();
  console.log('🔌 데이터베이스 연결 종료');
};
