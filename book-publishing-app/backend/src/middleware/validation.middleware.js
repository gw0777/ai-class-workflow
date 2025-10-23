import Joi from 'joi';

/**
 * 교재 생성/업데이트 검증
 */
export const validateTextbook = (req, res, next) => {
  const schema = Joi.object({
    title: Joi.string().required().min(1).max(200),
    subtitle: Joi.string().allow('', null).max(200),
    description: Joi.string().allow('', null).max(2000),
    author: Joi.string().required().min(1).max(100),
    language: Joi.string().valid('ko', 'en', 'ja', 'zh').default('ko'),
    isbn: Joi.string().allow('', null).pattern(/^(?:\d{10}|\d{13})$/),
    metadata: Joi.object({
      subject: Joi.string().required(),
      targetAudience: Joi.string().required(),
      difficulty: Joi.string().valid('beginner', 'intermediate', 'advanced').required(),
      keywords: Joi.array().items(Joi.string()).min(1)
    }).optional()
  });

  const { error, value } = schema.validate(req.body);

  if (error) {
    return res.status(400).json({
      success: false,
      error: '입력 데이터가 유효하지 않습니다.',
      details: error.details.map(detail => ({
        field: detail.path.join('.'),
        message: detail.message
      }))
    });
  }

  req.body = value;
  next();
};

/**
 * 챕터 검증
 */
export const validateChapter = (req, res, next) => {
  const schema = Joi.object({
    number: Joi.number().integer().min(1).required(),
    title: Joi.string().required().min(1).max(200),
    content: Joi.string().required().min(1),
    learningObjectives: Joi.array().items(Joi.string()).min(1).required(),
    summary: Joi.string().allow('', null),
    order: Joi.number().integer().min(0).required()
  });

  const { error, value } = schema.validate(req.body);

  if (error) {
    return res.status(400).json({
      success: false,
      error: '입력 데이터가 유효하지 않습니다.',
      details: error.details.map(detail => ({
        field: detail.path.join('.'),
        message: detail.message
      }))
    });
  }

  req.body = value;
  next();
};

/**
 * 출판 규정 검증
 */
export const validateRegulation = (req, res, next) => {
  const schema = Joi.object({
    title: Joi.string().required().min(1).max(200),
    description: Joi.string().allow('', null).max(500),
    content: Joi.string().required().min(1),
    category: Joi.string().valid(
      'COPYRIGHT',
      'ISBN',
      'FORMATTING',
      'CONTENT_STANDARD',
      'DISTRIBUTION',
      'QUALITY',
      'LEGAL'
    ).required(),
    country: Joi.string().length(2).uppercase().required(),
    version: Joi.string().required(),
    effectiveDate: Joi.date().required(),
    source: Joi.string().uri().allow('', null),
    tags: Joi.array().items(Joi.string()).optional()
  });

  const { error, value } = schema.validate(req.body);

  if (error) {
    return res.status(400).json({
      success: false,
      error: '입력 데이터가 유효하지 않습니다.',
      details: error.details.map(detail => ({
        field: detail.path.join('.'),
        message: detail.message
      }))
    });
  }

  req.body = value;
  next();
};

/**
 * 평가 문항 검증
 */
export const validateAssessment = (req, res, next) => {
  const schema = Joi.object({
    question: Joi.string().required().min(1),
    type: Joi.string().valid('MULTIPLE_CHOICE', 'TRUE_FALSE', 'SHORT_ANSWER', 'ESSAY').required(),
    options: Joi.when('type', {
      is: 'MULTIPLE_CHOICE',
      then: Joi.array().items(Joi.string()).min(2).required(),
      otherwise: Joi.optional()
    }),
    answer: Joi.string().required().min(1),
    explanation: Joi.string().allow('', null),
    difficulty: Joi.number().integer().min(1).max(5).default(3),
    points: Joi.number().integer().min(1).default(1)
  });

  const { error, value } = schema.validate(req.body);

  if (error) {
    return res.status(400).json({
      success: false,
      error: '입력 데이터가 유효하지 않습니다.',
      details: error.details.map(detail => ({
        field: detail.path.join('.'),
        message: detail.message
      }))
    });
  }

  req.body = value;
  next();
};

/**
 * 사용자 등록 검증
 */
export const validateUser = (req, res, next) => {
  const schema = Joi.object({
    email: Joi.string().email().required(),
    password: Joi.string().min(8).required()
      .pattern(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/)
      .message('비밀번호는 최소 8자 이상이며, 대문자, 소문자, 숫자를 포함해야 합니다.'),
    name: Joi.string().required().min(2).max(50),
    role: Joi.string().valid('ADMIN', 'EDITOR', 'REVIEWER', 'VIEWER').default('VIEWER')
  });

  const { error, value } = schema.validate(req.body);

  if (error) {
    return res.status(400).json({
      success: false,
      error: '입력 데이터가 유효하지 않습니다.',
      details: error.details.map(detail => ({
        field: detail.path.join('.'),
        message: detail.message
      }))
    });
  }

  req.body = value;
  next();
};

/**
 * 로그인 검증
 */
export const validateLogin = (req, res, next) => {
  const schema = Joi.object({
    email: Joi.string().email().required(),
    password: Joi.string().required()
  });

  const { error, value } = schema.validate(req.body);

  if (error) {
    return res.status(400).json({
      success: false,
      error: '입력 데이터가 유효하지 않습니다.',
      details: error.details.map(detail => ({
        field: detail.path.join('.'),
        message: detail.message
      }))
    });
  }

  req.body = value;
  next();
};
