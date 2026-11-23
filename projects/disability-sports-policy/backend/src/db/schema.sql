-- ============================================================================
-- 범용 정책 분석 플랫폼 - PostgreSQL 스키마
-- 6계층 아키텍처 중 데이터 저장 레이어 (구조화 메타데이터)
-- ============================================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- 텍스트 유사도 검색

-- ============================================================================
-- 1. 주제 템플릿 테이블 (Topic Templates)
-- ============================================================================
CREATE TABLE IF NOT EXISTS topic_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100), -- 예: '체육', '교육', '의료', '환경' 등

    -- 주제별 설정
    config JSONB NOT NULL DEFAULT '{}'::jsonb,
    -- {
    --   "keywords": ["장애인", "체육", "정책"],
    --   "sources": ["문화체육관광부", "대한장애인체육회"],
    --   "document_types": ["정책문서", "법령", "조례"],
    --   "nlp_config": {"language": "ko", "domain_dict": "sports"},
    --   "crawler_config": {"urls": [...], "selectors": {...}}
    -- }

    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_topic_templates_category ON topic_templates(category);
CREATE INDEX idx_topic_templates_active ON topic_templates(is_active);

-- ============================================================================
-- 2. 문서 소스 테이블 (Document Sources)
-- ============================================================================
CREATE TABLE IF NOT EXISTS document_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    topic_id UUID REFERENCES topic_templates(id) ON DELETE CASCADE,

    name VARCHAR(255) NOT NULL,
    source_type VARCHAR(50) NOT NULL, -- 'government', 'academic', 'international', 'local'
    url TEXT,
    api_endpoint TEXT,

    -- 크롤링 설정
    crawler_config JSONB,
    last_crawled_at TIMESTAMP,
    crawl_frequency_hours INTEGER DEFAULT 24,

    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_document_sources_topic ON document_sources(topic_id);
CREATE INDEX idx_document_sources_type ON document_sources(source_type);

-- ============================================================================
-- 3. 정책 문서 메타데이터 테이블 (Policy Documents)
-- ============================================================================
CREATE TABLE IF NOT EXISTS policy_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    topic_id UUID REFERENCES topic_templates(id) ON DELETE SET NULL,
    source_id UUID REFERENCES document_sources(id) ON DELETE SET NULL,

    -- 문서 기본 정보
    title VARCHAR(500) NOT NULL,
    title_en VARCHAR(500),
    document_type VARCHAR(100), -- '정책문서', '법령', '조례', '가이드라인', '연구보고서'

    -- 발행 정보
    publisher VARCHAR(255),
    author VARCHAR(255),
    publish_date DATE,

    -- 분류
    category VARCHAR(100),
    subcategory VARCHAR(100),
    tags TEXT[], -- 배열 타입으로 태그 저장
    keywords TEXT[],

    -- 문서 위치
    url TEXT,
    file_path TEXT,
    mongodb_id VARCHAR(24), -- MongoDB의 ObjectId 참조

    -- 처리 상태
    processing_status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    is_embedded BOOLEAN DEFAULT false, -- 벡터 임베딩 완료 여부

    -- 통계 정보
    page_count INTEGER,
    word_count INTEGER,
    language VARCHAR(10) DEFAULT 'ko',

    -- 검색 최적화 (GIN 인덱스용)
    search_vector tsvector,

    -- 메타데이터
    metadata JSONB DEFAULT '{}'::jsonb,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 생성
CREATE INDEX idx_policy_documents_topic ON policy_documents(topic_id);
CREATE INDEX idx_policy_documents_source ON policy_documents(source_id);
CREATE INDEX idx_policy_documents_type ON policy_documents(document_type);
CREATE INDEX idx_policy_documents_publisher ON policy_documents(publisher);
CREATE INDEX idx_policy_documents_date ON policy_documents(publish_date);
CREATE INDEX idx_policy_documents_status ON policy_documents(processing_status);
CREATE INDEX idx_policy_documents_embedded ON policy_documents(is_embedded);

-- GIN 인덱스 (배열 및 전문 검색)
CREATE INDEX idx_policy_documents_tags ON policy_documents USING GIN(tags);
CREATE INDEX idx_policy_documents_keywords ON policy_documents USING GIN(keywords);
CREATE INDEX idx_policy_documents_search ON policy_documents USING GIN(search_vector);

-- 텍스트 유사도 검색 인덱스
CREATE INDEX idx_policy_documents_title_trgm ON policy_documents USING gin(title gin_trgm_ops);

-- ============================================================================
-- 4. 문서 청크 테이블 (Document Chunks) - Vector DB 매핑용
-- ============================================================================
CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES policy_documents(id) ON DELETE CASCADE,

    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,

    -- Vector DB 참조
    vector_id VARCHAR(100), -- Qdrant의 포인트 ID
    embedding_model VARCHAR(100) DEFAULT 'multilingual-e5-large',

    -- 위치 정보
    start_position INTEGER,
    end_position INTEGER,
    page_number INTEGER,

    -- 메타데이터
    metadata JSONB DEFAULT '{}'::jsonb,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_document_chunks_document ON document_chunks(document_id);
CREATE INDEX idx_document_chunks_vector ON document_chunks(vector_id);

-- ============================================================================
-- 5. 분석 작업 테이블 (Analysis Jobs)
-- ============================================================================
CREATE TABLE IF NOT EXISTS analysis_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    topic_id UUID REFERENCES topic_templates(id) ON DELETE SET NULL,

    job_type VARCHAR(100) NOT NULL, -- 'rag_query', 'comparison', 'trend_analysis', 'entity_extraction'

    -- 작업 설정
    query TEXT,
    config JSONB DEFAULT '{}'::jsonb,

    -- 상태
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed'
    progress INTEGER DEFAULT 0,

    -- 결과
    result JSONB,
    error_message TEXT,

    -- Claude API 사용량
    claude_model VARCHAR(100),
    input_tokens INTEGER,
    output_tokens INTEGER,
    cached_tokens INTEGER,
    cost_usd DECIMAL(10, 6),

    -- 타이밍
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_ms INTEGER,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_analysis_jobs_topic ON analysis_jobs(topic_id);
CREATE INDEX idx_analysis_jobs_status ON analysis_jobs(status);
CREATE INDEX idx_analysis_jobs_type ON analysis_jobs(job_type);
CREATE INDEX idx_analysis_jobs_created ON analysis_jobs(created_at DESC);

-- ============================================================================
-- 6. 프롬프트 템플릿 테이블 (Prompt Templates)
-- ============================================================================
CREATE TABLE IF NOT EXISTS prompt_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    topic_id UUID REFERENCES topic_templates(id) ON DELETE CASCADE,

    name VARCHAR(255) NOT NULL,
    description TEXT,

    -- 프롬프트 내용
    system_prompt TEXT NOT NULL,
    user_prompt_template TEXT NOT NULL,

    -- 프롬프트 설정
    model VARCHAR(100) DEFAULT 'claude-3-5-sonnet-20241022',
    max_tokens INTEGER DEFAULT 4096,
    temperature DECIMAL(3, 2) DEFAULT 0.7,

    -- Prompt Caching 설정
    enable_caching BOOLEAN DEFAULT true,
    cache_ttl_minutes INTEGER DEFAULT 5,

    -- 성능 통계
    usage_count INTEGER DEFAULT 0,
    avg_input_tokens INTEGER,
    avg_output_tokens INTEGER,
    avg_response_time_ms INTEGER,

    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_prompt_templates_topic ON prompt_templates(topic_id);
CREATE INDEX idx_prompt_templates_active ON prompt_templates(is_active);

-- ============================================================================
-- 7. 엔티티 추출 테이블 (Named Entities)
-- ============================================================================
CREATE TABLE IF NOT EXISTS named_entities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES policy_documents(id) ON DELETE CASCADE,

    entity_type VARCHAR(100) NOT NULL, -- 'organization', 'law', 'program', 'budget', 'date', 'person'
    entity_text VARCHAR(500) NOT NULL,
    normalized_text VARCHAR(500),

    context TEXT, -- 엔티티가 나타난 문맥

    frequency INTEGER DEFAULT 1,
    confidence DECIMAL(5, 4),

    metadata JSONB DEFAULT '{}'::jsonb,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_named_entities_document ON named_entities(document_id);
CREATE INDEX idx_named_entities_type ON named_entities(entity_type);
CREATE INDEX idx_named_entities_text ON named_entities(entity_text);

-- ============================================================================
-- 8. 사용자 및 세션 관리 (선택적)
-- ============================================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'user', -- 'admin', 'user', 'guest'

    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(500) NOT NULL,

    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_sessions_user ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_token ON user_sessions(token);

-- ============================================================================
-- 트리거: updated_at 자동 업데이트
-- ============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_topic_templates_updated_at BEFORE UPDATE ON topic_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_document_sources_updated_at BEFORE UPDATE ON document_sources
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_policy_documents_updated_at BEFORE UPDATE ON policy_documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_prompt_templates_updated_at BEFORE UPDATE ON prompt_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 초기 데이터: 장애인 체육 주제 템플릿
-- ============================================================================
INSERT INTO topic_templates (name, display_name, description, category, config) VALUES
(
    'disability_sports',
    '장애인 체육 정책',
    '장애인 체육 진흥 정책, 법령, 조례 및 국제 기준 분석',
    '체육',
    '{
        "keywords": ["장애인", "체육", "생활체육", "전문체육", "반다비", "패럴림픽", "접근성"],
        "sources": [
            {"name": "문화체육관광부", "type": "government"},
            {"name": "대한장애인체육회", "type": "organization"},
            {"name": "국제패럴림픽위원회", "type": "international"}
        ],
        "document_types": ["정책문서", "법령", "조례", "가이드라인", "연구보고서"],
        "nlp_config": {
            "language": "ko",
            "domain_dict": "disability_sports",
            "entities": ["organization", "law", "program", "facility", "budget"]
        },
        "crawler_config": {
            "urls": [
                "https://www.mcst.go.kr",
                "https://www.koreanpc.kr",
                "https://www.paralympic.org"
            ]
        }
    }'::jsonb
)
ON CONFLICT (name) DO NOTHING;

-- ============================================================================
-- 뷰: 문서 검색 통합 뷰
-- ============================================================================
CREATE OR REPLACE VIEW v_document_search AS
SELECT
    pd.id,
    pd.title,
    pd.document_type,
    pd.publisher,
    pd.publish_date,
    pd.category,
    pd.tags,
    pd.keywords,
    pd.url,
    tt.display_name AS topic_name,
    ds.name AS source_name,
    pd.is_embedded,
    pd.created_at
FROM policy_documents pd
LEFT JOIN topic_templates tt ON pd.topic_id = tt.id
LEFT JOIN document_sources ds ON pd.source_id = ds.id
WHERE pd.processing_status = 'completed';

-- ============================================================================
-- 통계 뷰
-- ============================================================================
CREATE OR REPLACE VIEW v_topic_statistics AS
SELECT
    tt.id AS topic_id,
    tt.display_name AS topic_name,
    COUNT(pd.id) AS total_documents,
    SUM(CASE WHEN pd.is_embedded THEN 1 ELSE 0 END) AS embedded_documents,
    COUNT(DISTINCT pd.publisher) AS unique_publishers,
    MIN(pd.publish_date) AS earliest_date,
    MAX(pd.publish_date) AS latest_date,
    SUM(pd.word_count) AS total_words
FROM topic_templates tt
LEFT JOIN policy_documents pd ON tt.id = pd.topic_id
WHERE tt.is_active = true
GROUP BY tt.id, tt.display_name;

COMMENT ON TABLE topic_templates IS '주제 템플릿: 다양한 분야의 정책 분석을 위한 설정';
COMMENT ON TABLE policy_documents IS '정책 문서 메타데이터: 구조화된 검색 및 필터링';
COMMENT ON TABLE document_chunks IS '문서 청크: Vector DB 매핑 및 RAG용';
COMMENT ON TABLE analysis_jobs IS '분석 작업: Claude API 쿼리 및 결과 추적';
COMMENT ON TABLE prompt_templates IS '프롬프트 템플릿: 재사용 가능한 Claude 프롬프트';
