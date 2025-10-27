import express, { Router, Request, Response } from 'express';
import { ClaudeService } from '../services/claude/ClaudeService';
import { VectorService, DocumentEmbeddingService } from '../services/vector/VectorService';
import { TemplateService } from '../services/template/TemplateService';
import { PromptOptimizer } from '../services/template/TemplateService';

const router: Router = express.Router();
const claudeService = new ClaudeService();
const vectorService = new VectorService();
const documentEmbeddingService = new DocumentEmbeddingService(vectorService);
const templateService = new TemplateService();
const promptOptimizer = new PromptOptimizer();

/**
 * POST /api/rag/query
 * RAG 쿼리 실행
 */
router.post('/query', async (req: Request, res: Response) => {
  try {
    const {
      query,
      topicName,
      topK = 5,
      minScore = 0.7,
      model = 'sonnet',
      useCache = true,
    } = req.body;

    if (!query) {
      return res.status(400).json({
        success: false,
        error: {
          code: 'INVALID_INPUT',
          message: 'query 필드가 필요합니다.',
        },
      });
    }

    console.log(`[RAG] 쿼리 요청: ${query} (주제: ${topicName || '전체'})`);

    // 1. Vector DB에서 관련 문서 검색
    const retrievedDocs = await documentEmbeddingService.searchForRAG(
      query,
      topK,
      topicName ? { topicName } : undefined
    );

    if (retrievedDocs.length === 0) {
      return res.json({
        success: true,
        data: {
          answer: '관련된 정책 문서를 찾을 수 없습니다. 다른 키워드로 검색해보세요.',
          sources: [],
          confidence: 0,
          metadata: {
            model: '',
            inputTokens: 0,
            outputTokens: 0,
            cachedTokens: 0,
            responseTimeMs: 0,
            costUsd: 0,
          },
        },
      });
    }

    // 2. 시스템 프롬프트 생성
    const systemPrompt = topicName
      ? templateService.generateSystemPrompt(topicName)
      : '당신은 정책 분석 전문가입니다.';

    // 3. Claude API RAG 실행
    const result = await claudeService.ragQuery(
      query,
      retrievedDocs,
      systemPrompt,
      useCache,
      model
    );

    res.json({
      success: true,
      data: result,
    });
  } catch (error) {
    console.error('[RAG] 쿼리 실패:', error);
    res.status(500).json({
      success: false,
      error: {
        code: 'RAG_QUERY_ERROR',
        message: 'RAG 쿼리 실행 실패',
        details: error instanceof Error ? error.message : 'Unknown error',
      },
    });
  }
});

/**
 * POST /api/rag/search
 * 벡터 검색만 수행 (Claude API 호출 없이)
 */
router.post('/search', async (req: Request, res: Response) => {
  try {
    const { query, topK = 5, filters } = req.body;

    if (!query) {
      return res.status(400).json({
        success: false,
        error: {
          code: 'INVALID_INPUT',
          message: 'query 필드가 필요합니다.',
        },
      });
    }

    const results = await documentEmbeddingService.searchForRAG(
      query,
      topK,
      filters
    );

    res.json({
      success: true,
      data: {
        results,
        total: results.length,
      },
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: {
        code: 'VECTOR_SEARCH_ERROR',
        message: '벡터 검색 실패',
      },
    });
  }
});

/**
 * POST /api/rag/compare
 * 정책 비교 분석
 */
router.post('/compare', async (req: Request, res: Response) => {
  try {
    const { policies, criteria } = req.body;

    if (!policies || !Array.isArray(policies) || policies.length < 2) {
      return res.status(400).json({
        success: false,
        error: {
          code: 'INVALID_INPUT',
          message: '최소 2개 이상의 정책이 필요합니다.',
        },
      });
    }

    const result = await claudeService.comparePolicies(
      policies,
      criteria || ['목적', '내용', '예산', '대상']
    );

    res.json({
      success: true,
      data: {
        comparison: result,
      },
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: {
        code: 'COMPARISON_ERROR',
        message: '정책 비교 실패',
      },
    });
  }
});

/**
 * POST /api/rag/trend
 * 트렌드 분석
 */
router.post('/trend', async (req: Request, res: Response) => {
  try {
    const { documents } = req.body;

    if (!documents || !Array.isArray(documents)) {
      return res.status(400).json({
        success: false,
        error: {
          code: 'INVALID_INPUT',
          message: 'documents 배열이 필요합니다.',
        },
      });
    }

    const result = await claudeService.analyzeTrend(documents);

    res.json({
      success: true,
      data: {
        analysis: result,
      },
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: {
        code: 'TREND_ANALYSIS_ERROR',
        message: '트렌드 분석 실패',
      },
    });
  }
});

/**
 * POST /api/rag/prompt/evaluate
 * 프롬프트 평가
 */
router.post('/prompt/evaluate', async (req: Request, res: Response) => {
  try {
    const { prompt } = req.body;

    if (!prompt) {
      return res.status(400).json({
        success: false,
        error: {
          code: 'INVALID_INPUT',
          message: 'prompt 필드가 필요합니다.',
        },
      });
    }

    const evaluation = await promptOptimizer.evaluatePrompt(prompt);

    res.json({
      success: true,
      data: evaluation,
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: {
        code: 'PROMPT_EVALUATION_ERROR',
        message: '프롬프트 평가 실패',
      },
    });
  }
});

/**
 * POST /api/rag/prompt/improve
 * 프롬프트 개선
 */
router.post('/prompt/improve', async (req: Request, res: Response) => {
  try {
    const { prompt } = req.body;

    if (!prompt) {
      return res.status(400).json({
        success: false,
        error: {
          code: 'INVALID_INPUT',
          message: 'prompt 필드가 필요합니다.',
        },
      });
    }

    const improvedPrompt = await promptOptimizer.improvePrompt(prompt);

    res.json({
      success: true,
      data: {
        original: prompt,
        improved: improvedPrompt,
      },
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: {
        code: 'PROMPT_IMPROVEMENT_ERROR',
        message: '프롬프트 개선 실패',
      },
    });
  }
});

export default router;
