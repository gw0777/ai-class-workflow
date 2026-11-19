import { PrismaClient } from '@prisma/client';
import { convertPDFToTextbook } from '../services/pdfConverter.js';
import { convertPPTXToTextbook } from '../services/pptxConverter.js';
import fs from 'fs/promises';
import path from 'path';

const prisma = new PrismaClient();

/**
 * 파일 업로드 및 소스 자료로 저장
 */
export const uploadSourceMaterial = async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({
        success: false,
        error: '파일이 업로드되지 않았습니다.',
      });
    }

    const { originalname, filename, mimetype, size, path: filePath } = req.file;

    // 소스 자료 데이터베이스에 저장
    const sourceMaterial = await prisma.sourceMaterial.create({
      data: {
        filename: originalname,
        originalPath: filePath,
        fileType: mimetype,
        fileSize: size,
        metadata: {
          uploadedBy: req.user?.id,
        },
      },
    });

    res.status(201).json({
      success: true,
      message: '파일이 성공적으로 업로드되었습니다.',
      data: sourceMaterial,
    });
  } catch (error) {
    console.error('파일 업로드 오류:', error);
    res.status(500).json({
      success: false,
      error: '파일 업로드 중 오류가 발생했습니다.',
      details: error.message,
    });
  }
};

/**
 * PDF 파일을 교재로 변환
 */
export const convertPDFToTextbookController = async (req, res) => {
  try {
    const { sourceId } = req.params;
    const metadata = req.body;

    // 소스 자료 조회
    const sourceMaterial = await prisma.sourceMaterial.findUnique({
      where: { id: sourceId },
    });

    if (!sourceMaterial) {
      return res.status(404).json({
        success: false,
        error: '소스 자료를 찾을 수 없습니다.',
      });
    }

    if (!sourceMaterial.fileType.includes('pdf')) {
      return res.status(400).json({
        success: false,
        error: 'PDF 파일만 변환할 수 있습니다.',
      });
    }

    // PDF를 교재 데이터로 변환
    const textbookData = await convertPDFToTextbook(
      sourceMaterial.originalPath,
      metadata
    );

    // 교재 생성
    const textbook = await prisma.textbook.create({
      data: {
        ...textbookData,
        editorId: req.user.id,
        status: 'DRAFT',
        metadata: {
          create: textbookData.metadata,
        },
        chapters: {
          create: textbookData.chapters.map((chapter) => ({
            number: chapter.number,
            title: chapter.title,
            content: chapter.content,
            learningObjectives: chapter.learningObjectives,
            summary: chapter.summary,
            order: chapter.order,
            sections: {
              create: chapter.sections?.map((section) => ({
                title: section.title,
                content: section.content,
                order: section.order,
              })) || [],
            },
          })),
        },
      },
      include: {
        metadata: true,
        chapters: {
          include: {
            sections: true,
          },
        },
      },
    });

    // 소스 자료 처리 완료 표시
    await prisma.sourceMaterial.update({
      where: { id: sourceId },
      data: {
        processedAt: new Date(),
        metadata: {
          ...sourceMaterial.metadata,
          textbookId: textbook.id,
        },
      },
    });

    res.status(201).json({
      success: true,
      message: 'PDF가 성공적으로 교재로 변환되었습니다.',
      data: textbook,
    });
  } catch (error) {
    console.error('PDF 변환 오류:', error);
    res.status(500).json({
      success: false,
      error: 'PDF 변환 중 오류가 발생했습니다.',
      details: error.message,
    });
  }
};

/**
 * PPTX 파일을 교재로 변환
 */
export const convertPPTXToTextbookController = async (req, res) => {
  try {
    const { sourceId } = req.params;
    const metadata = req.body;

    // 소스 자료 조회
    const sourceMaterial = await prisma.sourceMaterial.findUnique({
      where: { id: sourceId },
    });

    if (!sourceMaterial) {
      return res.status(404).json({
        success: false,
        error: '소스 자료를 찾을 수 없습니다.',
      });
    }

    if (!sourceMaterial.fileType.includes('presentation') &&
        !sourceMaterial.fileType.includes('powerpoint')) {
      return res.status(400).json({
        success: false,
        error: 'PPTX 파일만 변환할 수 있습니다.',
      });
    }

    // PPTX를 교재 데이터로 변환
    const textbookData = await convertPPTXToTextbook(
      sourceMaterial.originalPath,
      metadata
    );

    // 교재 생성
    const textbook = await prisma.textbook.create({
      data: {
        ...textbookData,
        editorId: req.user.id,
        status: 'DRAFT',
        metadata: {
          create: textbookData.metadata,
        },
        chapters: {
          create: textbookData.chapters.map((chapter) => ({
            number: chapter.number,
            title: chapter.title,
            content: chapter.content,
            learningObjectives: chapter.learningObjectives,
            summary: chapter.summary,
            order: chapter.order,
            sections: {
              create: chapter.sections?.map((section) => ({
                title: section.title,
                content: section.content,
                order: section.order,
              })) || [],
            },
          })),
        },
      },
      include: {
        metadata: true,
        chapters: {
          include: {
            sections: true,
          },
        },
      },
    });

    // 소스 자료 처리 완료 표시
    await prisma.sourceMaterial.update({
      where: { id: sourceId },
      data: {
        processedAt: new Date(),
        metadata: {
          ...sourceMaterial.metadata,
          textbookId: textbook.id,
        },
      },
    });

    res.status(201).json({
      success: true,
      message: 'PPTX가 성공적으로 교재로 변환되었습니다.',
      data: textbook,
    });
  } catch (error) {
    console.error('PPTX 변환 오류:', error);
    res.status(500).json({
      success: false,
      error: 'PPTX 변환 중 오류가 발생했습니다.',
      details: error.message,
    });
  }
};

/**
 * 모든 소스 자료 조회
 */
export const getAllSourceMaterials = async (req, res) => {
  try {
    const { page = 1, limit = 10 } = req.query;
    const skip = (page - 1) * limit;

    const [materials, total] = await Promise.all([
      prisma.sourceMaterial.findMany({
        skip: parseInt(skip),
        take: parseInt(limit),
        orderBy: {
          uploadedAt: 'desc',
        },
      }),
      prisma.sourceMaterial.count(),
    ]);

    res.json({
      success: true,
      data: materials,
      pagination: {
        page: parseInt(page),
        limit: parseInt(limit),
        total,
        totalPages: Math.ceil(total / limit),
      },
    });
  } catch (error) {
    console.error('소스 자료 조회 오류:', error);
    res.status(500).json({
      success: false,
      error: '소스 자료 조회 중 오류가 발생했습니다.',
      details: error.message,
    });
  }
};

/**
 * 소스 자료 삭제
 */
export const deleteSourceMaterial = async (req, res) => {
  try {
    const { id } = req.params;

    const sourceMaterial = await prisma.sourceMaterial.findUnique({
      where: { id },
    });

    if (!sourceMaterial) {
      return res.status(404).json({
        success: false,
        error: '소스 자료를 찾을 수 없습니다.',
      });
    }

    // 파일 삭제
    try {
      await fs.unlink(sourceMaterial.originalPath);
    } catch (err) {
      console.warn('파일 삭제 실패:', err);
    }

    // 데이터베이스에서 삭제
    await prisma.sourceMaterial.delete({
      where: { id },
    });

    res.json({
      success: true,
      message: '소스 자료가 성공적으로 삭제되었습니다.',
    });
  } catch (error) {
    console.error('소스 자료 삭제 오류:', error);
    res.status(500).json({
      success: false,
      error: '소스 자료 삭제 중 오류가 발생했습니다.',
      details: error.message,
    });
  }
};
