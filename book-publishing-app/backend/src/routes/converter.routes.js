import express from 'express';
import multer from 'multer';
import path from 'path';
import {
  uploadSourceMaterial,
  convertPDFToTextbookController,
  convertPPTXToTextbookController,
  getAllSourceMaterials,
  deleteSourceMaterial,
} from '../controllers/converter.controller.js';
import { authenticate, authorize } from '../middleware/auth.middleware.js';

const router = express.Router();

// Multer 설정
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, 'uploads/');
  },
  filename: (req, file, cb) => {
    const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1e9);
    cb(null, file.fieldname + '-' + uniqueSuffix + path.extname(file.originalname));
  },
});

const fileFilter = (req, file, cb) => {
  const allowedTypes = [
    'application/pdf',
    'application/vnd.ms-powerpoint',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  ];

  if (allowedTypes.includes(file.mimetype)) {
    cb(null, true);
  } else {
    cb(new Error('지원하지 않는 파일 형식입니다. PDF, PPTX, DOCX만 업로드 가능합니다.'));
  }
};

const upload = multer({
  storage,
  fileFilter,
  limits: {
    fileSize: parseInt(process.env.MAX_FILE_SIZE) || 52428800, // 50MB
  },
});

// 소스 자료 업로드
router.post('/upload', authenticate, authorize(['ADMIN', 'EDITOR']), upload.single('file'), uploadSourceMaterial);

// 소스 자료 목록 조회
router.get('/materials', authenticate, getAllSourceMaterials);

// 소스 자료 삭제
router.delete('/materials/:id', authenticate, authorize(['ADMIN', 'EDITOR']), deleteSourceMaterial);

// PDF를 교재로 변환
router.post('/convert/pdf/:sourceId', authenticate, authorize(['ADMIN', 'EDITOR']), convertPDFToTextbookController);

// PPTX를 교재로 변환
router.post('/convert/pptx/:sourceId', authenticate, authorize(['ADMIN', 'EDITOR']), convertPPTXToTextbookController);

export default router;
