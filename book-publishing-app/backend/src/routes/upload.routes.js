import express from 'express';
import multer from 'multer';
import path from 'path';
import { authenticate } from '../middleware/auth.middleware.js';

const router = express.Router();

// 파일 업로드 설정
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, 'uploads/');
  },
  filename: (req, file, cb) => {
    const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
    cb(null, file.fieldname + '-' + uniqueSuffix + path.extname(file.originalname));
  }
});

const upload = multer({
  storage,
  limits: {
    fileSize: 50 * 1024 * 1024 // 50MB
  },
  fileFilter: (req, file, cb) => {
    const allowedTypes = /pdf|docx|pptx|jpg|jpeg|png/;
    const extname = allowedTypes.test(path.extname(file.originalname).toLowerCase());
    const mimetype = allowedTypes.test(file.mimetype);

    if (extname && mimetype) {
      return cb(null, true);
    } else {
      cb(new Error('지원하지 않는 파일 형식입니다.'));
    }
  }
});

// PDF/PPTX 업로드 및 변환
router.post('/source-material', authenticate, upload.single('file'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({
        success: false,
        error: '파일이 업로드되지 않았습니다.'
      });
    }

    res.json({
      success: true,
      message: '파일이 성공적으로 업로드되었습니다.',
      data: {
        filename: req.file.filename,
        originalName: req.file.originalname,
        size: req.file.size,
        path: req.file.path
      }
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: '파일 업로드 중 오류가 발생했습니다.',
      details: error.message
    });
  }
});

// 이미지 업로드 (표지 등)
router.post('/image', authenticate, upload.single('image'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({
        success: false,
        error: '이미지가 업로드되지 않았습니다.'
      });
    }

    res.json({
      success: true,
      message: '이미지가 성공적으로 업로드되었습니다.',
      data: {
        filename: req.file.filename,
        url: `/uploads/${req.file.filename}`
      }
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: '이미지 업로드 중 오류가 발생했습니다.',
      details: error.message
    });
  }
});

export default router;
