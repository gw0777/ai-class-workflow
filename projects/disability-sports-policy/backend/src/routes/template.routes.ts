import express, { Router, Request, Response } from 'express';
import { TemplateService } from '../services/template/TemplateService';

const router: Router = express.Router();
const templateService = new TemplateService();

/**
 * GET /api/templates
 * 모든 주제 템플릿 목록 조회
 */
router.get('/', async (req: Request, res: Response) => {
  try {
    const templates = templateService.getAllTemplates();

    res.json({
      success: true,
      data: templates,
      metadata: {
        total: templates.length,
        timestamp: new Date().toISOString(),
      },
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: {
        code: 'TEMPLATE_FETCH_ERROR',
        message: '템플릿 조회 실패',
      },
    });
  }
});

/**
 * GET /api/templates/:name
 * 특정 주제 템플릿 조회
 */
router.get('/:name', async (req: Request, res: Response) => {
  try {
    const { name } = req.params;
    const template = templateService.getTemplate(name);

    if (!template) {
      return res.status(404).json({
        success: false,
        error: {
          code: 'TEMPLATE_NOT_FOUND',
          message: `템플릿을 찾을 수 없습니다: ${name}`,
        },
      });
    }

    res.json({
      success: true,
      data: template,
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: {
        code: 'TEMPLATE_FETCH_ERROR',
        message: '템플릿 조회 실패',
      },
    });
  }
});

/**
 * GET /api/templates/category/:category
 * 카테고리별 템플릿 목록 조회
 */
router.get('/category/:category', async (req: Request, res: Response) => {
  try {
    const { category } = req.params;
    const templates = templateService.getTemplatesByCategory(category);

    res.json({
      success: true,
      data: templates,
      metadata: {
        category,
        total: templates.length,
        timestamp: new Date().toISOString(),
      },
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: {
        code: 'TEMPLATE_FETCH_ERROR',
        message: '템플릿 조회 실패',
      },
    });
  }
});

/**
 * POST /api/templates/create
 * AI 기반 새로운 주제 템플릿 생성
 */
router.post('/create', async (req: Request, res: Response) => {
  try {
    const { name, displayName, description, category } = req.body;

    if (!name || !displayName || !description || !category) {
      return res.status(400).json({
        success: false,
        error: {
          code: 'INVALID_INPUT',
          message: '필수 필드가 누락되었습니다.',
        },
      });
    }

    const template = await templateService.createTemplateFromDescription(
      name,
      displayName,
      description,
      category
    );

    res.status(201).json({
      success: true,
      data: template,
      message: '템플릿이 성공적으로 생성되었습니다.',
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: {
        code: 'TEMPLATE_CREATE_ERROR',
        message: '템플릿 생성 실패',
      },
    });
  }
});

/**
 * GET /api/templates/:name/system-prompt
 * 주제별 시스템 프롬프트 생성
 */
router.get('/:name/system-prompt', async (req: Request, res: Response) => {
  try {
    const { name } = req.params;
    const systemPrompt = templateService.generateSystemPrompt(name);

    res.json({
      success: true,
      data: {
        systemPrompt,
      },
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: {
        code: 'PROMPT_GENERATION_ERROR',
        message: '시스템 프롬프트 생성 실패',
      },
    });
  }
});

/**
 * GET /api/templates/:name/keywords
 * 주제별 도메인 키워드 조회
 */
router.get('/:name/keywords', async (req: Request, res: Response) => {
  try {
    const { name } = req.params;
    const keywords = templateService.getDomainKeywords(name);

    res.json({
      success: true,
      data: {
        keywords,
      },
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: {
        code: 'KEYWORDS_FETCH_ERROR',
        message: '키워드 조회 실패',
      },
    });
  }
});

export default router;
