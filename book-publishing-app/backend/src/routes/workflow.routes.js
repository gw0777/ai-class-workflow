import express from 'express';
import { authenticate } from '../middleware/auth.middleware.js';

const router = express.Router();

// 출판 워크플로우 관리 라우트
router.post('/textbooks/:id/workflow', authenticate, async (req, res) => {
  res.json({ message: '워크플로우 생성 기능 - 구현 예정' });
});

router.get('/textbooks/:id/workflow', async (req, res) => {
  res.json({ message: '워크플로우 조회 기능 - 구현 예정' });
});

router.put('/textbooks/:id/workflow/steps/:stepId', authenticate, async (req, res) => {
  res.json({ message: '워크플로우 단계 업데이트 기능 - 구현 예정' });
});

export default router;
