import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

/**
 * 출판 규정 생성
 */
export const createRegulation = async (req, res) => {
  try {
    const {
      title,
      description,
      content,
      category,
      country,
      version,
      effectiveDate,
      source,
      tags
    } = req.body;

    const regulation = await prisma.publishingRegulation.create({
      data: {
        title,
        description,
        content,
        category,
        country,
        version,
        effectiveDate: new Date(effectiveDate),
        source,
        isActive: true,
        ...(tags && {
          tags: {
            connectOrCreate: tags.map(tag => ({
              where: { name: tag },
              create: { name: tag }
            }))
          }
        })
      },
      include: {
        tags: true
      }
    });

    res.status(201).json({
      success: true,
      message: '출판 규정이 성공적으로 생성되었습니다.',
      data: regulation
    });
  } catch (error) {
    console.error('출판 규정 생성 오류:', error);
    res.status(500).json({
      success: false,
      error: '출판 규정 생성 중 오류가 발생했습니다.',
      details: error.message
    });
  }
};

/**
 * 모든 출판 규정 조회
 */
export const getAllRegulations = async (req, res) => {
  try {
    const {
      page = 1,
      limit = 20,
      isActive
    } = req.query;

    const skip = (page - 1) * limit;
    const where = {};

    if (isActive !== undefined) {
      where.isActive = isActive === 'true';
    }

    const [regulations, total] = await Promise.all([
      prisma.publishingRegulation.findMany({
        where,
        skip: parseInt(skip),
        take: parseInt(limit),
        include: {
          tags: true
        },
        orderBy: {
          effectiveDate: 'desc'
        }
      }),
      prisma.publishingRegulation.count({ where })
    ]);

    res.json({
      success: true,
      data: regulations,
      pagination: {
        page: parseInt(page),
        limit: parseInt(limit),
        total,
        totalPages: Math.ceil(total / limit)
      }
    });
  } catch (error) {
    console.error('출판 규정 조회 오류:', error);
    res.status(500).json({
      success: false,
      error: '출판 규정 조회 중 오류가 발생했습니다.',
      details: error.message
    });
  }
};

/**
 * ID로 출판 규정 조회
 */
export const getRegulationById = async (req, res) => {
  try {
    const { id } = req.params;

    const regulation = await prisma.publishingRegulation.findUnique({
      where: { id },
      include: {
        tags: true
      }
    });

    if (!regulation) {
      return res.status(404).json({
        success: false,
        error: '출판 규정을 찾을 수 없습니다.'
      });
    }

    res.json({
      success: true,
      data: regulation
    });
  } catch (error) {
    console.error('출판 규정 조회 오류:', error);
    res.status(500).json({
      success: false,
      error: '출판 규정 조회 중 오류가 발생했습니다.',
      details: error.message
    });
  }
};

/**
 * 출판 규정 업데이트
 */
export const updateRegulation = async (req, res) => {
  try {
    const { id } = req.params;
    const updateData = req.body;

    // 태그 별도 처리
    const { tags, ...regulationData } = updateData;

    const regulation = await prisma.publishingRegulation.update({
      where: { id },
      data: {
        ...regulationData,
        ...(tags && {
          tags: {
            set: [], // 기존 태그 제거
            connectOrCreate: tags.map(tag => ({
              where: { name: tag },
              create: { name: tag }
            }))
          }
        })
      },
      include: {
        tags: true
      }
    });

    res.json({
      success: true,
      message: '출판 규정이 성공적으로 업데이트되었습니다.',
      data: regulation
    });
  } catch (error) {
    console.error('출판 규정 업데이트 오류:', error);
    res.status(500).json({
      success: false,
      error: '출판 규정 업데이트 중 오류가 발생했습니다.',
      details: error.message
    });
  }
};

/**
 * 출판 규정 삭제
 */
export const deleteRegulation = async (req, res) => {
  try {
    const { id } = req.params;

    await prisma.publishingRegulation.delete({
      where: { id }
    });

    res.json({
      success: true,
      message: '출판 규정이 성공적으로 삭제되었습니다.'
    });
  } catch (error) {
    console.error('출판 규정 삭제 오류:', error);
    res.status(500).json({
      success: false,
      error: '출판 규정 삭제 중 오류가 발생했습니다.',
      details: error.message
    });
  }
};

/**
 * 출판 규정 검색
 */
export const searchRegulations = async (req, res) => {
  try {
    const { q, category, country } = req.query;

    const where = {
      isActive: true,
      AND: []
    };

    if (q) {
      where.AND.push({
        OR: [
          { title: { contains: q, mode: 'insensitive' } },
          { description: { contains: q, mode: 'insensitive' } },
          { content: { contains: q, mode: 'insensitive' } }
        ]
      });
    }

    if (category) {
      where.AND.push({ category });
    }

    if (country) {
      where.AND.push({ country });
    }

    const regulations = await prisma.publishingRegulation.findMany({
      where,
      include: {
        tags: true
      },
      orderBy: {
        effectiveDate: 'desc'
      }
    });

    res.json({
      success: true,
      data: regulations,
      count: regulations.length
    });
  } catch (error) {
    console.error('출판 규정 검색 오류:', error);
    res.status(500).json({
      success: false,
      error: '출판 규정 검색 중 오류가 발생했습니다.',
      details: error.message
    });
  }
};

/**
 * 카테고리별 출판 규정 조회
 */
export const getRegulationsByCategory = async (req, res) => {
  try {
    const { category } = req.params;

    const regulations = await prisma.publishingRegulation.findMany({
      where: {
        category,
        isActive: true
      },
      include: {
        tags: true
      },
      orderBy: {
        effectiveDate: 'desc'
      }
    });

    res.json({
      success: true,
      data: regulations,
      category
    });
  } catch (error) {
    console.error('카테고리별 출판 규정 조회 오류:', error);
    res.status(500).json({
      success: false,
      error: '출판 규정 조회 중 오류가 발생했습니다.',
      details: error.message
    });
  }
};

/**
 * 국가별 출판 규정 조회
 */
export const getRegulationsByCountry = async (req, res) => {
  try {
    const { country } = req.params;

    const regulations = await prisma.publishingRegulation.findMany({
      where: {
        country,
        isActive: true
      },
      include: {
        tags: true
      },
      orderBy: {
        effectiveDate: 'desc'
      }
    });

    res.json({
      success: true,
      data: regulations,
      country
    });
  } catch (error) {
    console.error('국가별 출판 규정 조회 오류:', error);
    res.status(500).json({
      success: false,
      error: '출판 규정 조회 중 오류가 발생했습니다.',
      details: error.message
    });
  }
};
