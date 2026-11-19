import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

/**
 * 새 교재 생성
 */
export const createTextbook = async (req, res) => {
  try {
    const {
      title,
      subtitle,
      description,
      author,
      language = 'ko',
      metadata
    } = req.body;

    const textbook = await prisma.textbook.create({
      data: {
        title,
        subtitle,
        description,
        author,
        language,
        editorId: req.user.id,
        status: 'DRAFT',
        ...(metadata && {
          metadata: {
            create: metadata
          }
        })
      },
      include: {
        metadata: true,
        editor: {
          select: {
            id: true,
            name: true,
            email: true
          }
        }
      }
    });

    res.status(201).json({
      success: true,
      message: '교재가 성공적으로 생성되었습니다.',
      data: textbook
    });
  } catch (error) {
    console.error('교재 생성 오류:', error);
    res.status(500).json({
      success: false,
      error: '교재 생성 중 오류가 발생했습니다.',
      details: error.message
    });
  }
};

/**
 * 모든 교재 조회
 */
export const getAllTextbooks = async (req, res) => {
  try {
    const {
      page = 1,
      limit = 10,
      status,
      language,
      search
    } = req.query;

    const skip = (page - 1) * limit;
    const where = {};

    if (status) where.status = status;
    if (language) where.language = language;
    if (search) {
      where.OR = [
        { title: { contains: search, mode: 'insensitive' } },
        { author: { contains: search, mode: 'insensitive' } },
        { description: { contains: search, mode: 'insensitive' } }
      ];
    }

    const [textbooks, total] = await Promise.all([
      prisma.textbook.findMany({
        where,
        skip: parseInt(skip),
        take: parseInt(limit),
        include: {
          editor: {
            select: {
              id: true,
              name: true,
              email: true
            }
          },
          metadata: true,
          _count: {
            select: {
              chapters: true
            }
          }
        },
        orderBy: {
          createdAt: 'desc'
        }
      }),
      prisma.textbook.count({ where })
    ]);

    res.json({
      success: true,
      data: textbooks,
      pagination: {
        page: parseInt(page),
        limit: parseInt(limit),
        total,
        totalPages: Math.ceil(total / limit)
      }
    });
  } catch (error) {
    console.error('교재 조회 오류:', error);
    res.status(500).json({
      success: false,
      error: '교재 조회 중 오류가 발생했습니다.',
      details: error.message
    });
  }
};

/**
 * ID로 교재 조회
 */
export const getTextbookById = async (req, res) => {
  try {
    const { id } = req.params;

    const textbook = await prisma.textbook.findUnique({
      where: { id },
      include: {
        editor: {
          select: {
            id: true,
            name: true,
            email: true
          }
        },
        metadata: true,
        chapters: {
          include: {
            sections: true,
            assessments: true
          },
          orderBy: {
            order: 'asc'
          }
        },
        workflow: {
          include: {
            steps: {
              include: {
                assignee: {
                  select: {
                    id: true,
                    name: true,
                    email: true
                  }
                }
              },
              orderBy: {
                createdAt: 'asc'
              }
            }
          }
        }
      }
    });

    if (!textbook) {
      return res.status(404).json({
        success: false,
        error: '교재를 찾을 수 없습니다.'
      });
    }

    res.json({
      success: true,
      data: textbook
    });
  } catch (error) {
    console.error('교재 조회 오류:', error);
    res.status(500).json({
      success: false,
      error: '교재 조회 중 오류가 발생했습니다.',
      details: error.message
    });
  }
};

/**
 * 교재 업데이트
 */
export const updateTextbook = async (req, res) => {
  try {
    const { id } = req.params;
    const updateData = req.body;

    // 메타데이터 별도 처리
    const { metadata, ...textbookData } = updateData;

    const textbook = await prisma.textbook.update({
      where: { id },
      data: {
        ...textbookData,
        ...(metadata && {
          metadata: {
            upsert: {
              create: metadata,
              update: metadata
            }
          }
        })
      },
      include: {
        metadata: true,
        editor: {
          select: {
            id: true,
            name: true,
            email: true
          }
        }
      }
    });

    res.json({
      success: true,
      message: '교재가 성공적으로 업데이트되었습니다.',
      data: textbook
    });
  } catch (error) {
    console.error('교재 업데이트 오류:', error);
    res.status(500).json({
      success: false,
      error: '교재 업데이트 중 오류가 발생했습니다.',
      details: error.message
    });
  }
};

/**
 * 교재 삭제
 */
export const deleteTextbook = async (req, res) => {
  try {
    const { id } = req.params;

    await prisma.textbook.delete({
      where: { id }
    });

    res.json({
      success: true,
      message: '교재가 성공적으로 삭제되었습니다.'
    });
  } catch (error) {
    console.error('교재 삭제 오류:', error);
    res.status(500).json({
      success: false,
      error: '교재 삭제 중 오류가 발생했습니다.',
      details: error.message
    });
  }
};

/**
 * 교재 출판
 */
export const publishTextbook = async (req, res) => {
  try {
    const { id } = req.params;

    const textbook = await prisma.textbook.update({
      where: { id },
      data: {
        status: 'PUBLISHED',
        publishedAt: new Date()
      }
    });

    res.json({
      success: true,
      message: '교재가 성공적으로 출판되었습니다.',
      data: textbook
    });
  } catch (error) {
    console.error('교재 출판 오류:', error);
    res.status(500).json({
      success: false,
      error: '교재 출판 중 오류가 발생했습니다.',
      details: error.message
    });
  }
};

/**
 * 챕터 추가
 */
export const addChapter = async (req, res) => {
  try {
    const { id } = req.params;
    const {
      number,
      title,
      content,
      learningObjectives,
      summary,
      order
    } = req.body;

    const chapter = await prisma.chapter.create({
      data: {
        textbookId: id,
        number,
        title,
        content,
        learningObjectives,
        summary,
        order
      }
    });

    res.status(201).json({
      success: true,
      message: '챕터가 성공적으로 추가되었습니다.',
      data: chapter
    });
  } catch (error) {
    console.error('챕터 추가 오류:', error);
    res.status(500).json({
      success: false,
      error: '챕터 추가 중 오류가 발생했습니다.',
      details: error.message
    });
  }
};

/**
 * 챕터 업데이트
 */
export const updateChapter = async (req, res) => {
  try {
    const { chapterId } = req.params;
    const updateData = req.body;

    const chapter = await prisma.chapter.update({
      where: { id: chapterId },
      data: updateData
    });

    res.json({
      success: true,
      message: '챕터가 성공적으로 업데이트되었습니다.',
      data: chapter
    });
  } catch (error) {
    console.error('챕터 업데이트 오류:', error);
    res.status(500).json({
      success: false,
      error: '챕터 업데이트 중 오류가 발생했습니다.',
      details: error.message
    });
  }
};

/**
 * 챕터 삭제
 */
export const deleteChapter = async (req, res) => {
  try {
    const { chapterId } = req.params;

    await prisma.chapter.delete({
      where: { id: chapterId }
    });

    res.json({
      success: true,
      message: '챕터가 성공적으로 삭제되었습니다.'
    });
  } catch (error) {
    console.error('챕터 삭제 오류:', error);
    res.status(500).json({
      success: false,
      error: '챕터 삭제 중 오류가 발생했습니다.',
      details: error.message
    });
  }
};

/**
 * 평가 문항 추가
 */
export const addAssessment = async (req, res) => {
  try {
    const { chapterId } = req.params;
    const {
      question,
      type,
      options,
      answer,
      explanation,
      difficulty,
      points
    } = req.body;

    const assessment = await prisma.assessment.create({
      data: {
        chapterId,
        question,
        type,
        options,
        answer,
        explanation,
        difficulty,
        points
      }
    });

    res.status(201).json({
      success: true,
      message: '평가 문항이 성공적으로 추가되었습니다.',
      data: assessment
    });
  } catch (error) {
    console.error('평가 문항 추가 오류:', error);
    res.status(500).json({
      success: false,
      error: '평가 문항 추가 중 오류가 발생했습니다.',
      details: error.message
    });
  }
};
