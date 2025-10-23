import express from 'express';
import {
  createTextbook,
  getAllTextbooks,
  getTextbookById,
  updateTextbook,
  deleteTextbook,
  publishTextbook,
  addChapter,
  updateChapter,
  deleteChapter,
  addAssessment
} from '../controllers/textbook.controller.js';
import { authenticate } from '../middleware/auth.middleware.js';
import { validateTextbook } from '../middleware/validation.middleware.js';

const router = express.Router();

// 교재 CRUD
router.post('/', authenticate, validateTextbook, createTextbook);
router.get('/', getAllTextbooks);
router.get('/:id', getTextbookById);
router.put('/:id', authenticate, updateTextbook);
router.delete('/:id', authenticate, deleteTextbook);

// 교재 출판
router.post('/:id/publish', authenticate, publishTextbook);

// 챕터 관리
router.post('/:id/chapters', authenticate, addChapter);
router.put('/:id/chapters/:chapterId', authenticate, updateChapter);
router.delete('/:id/chapters/:chapterId', authenticate, deleteChapter);

// 평가 문항 추가
router.post('/:id/chapters/:chapterId/assessments', authenticate, addAssessment);

export default router;
