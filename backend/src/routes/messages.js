import express from 'express';
import { MessageController } from '../controllers/messageController.js';
import { authenticateToken, requireProfessor, requireStudent } from '../middleware/auth.js';

const router = express.Router();

// 메시지 AI 분석 (교수용)
router.post('/analyze', authenticateToken, requireProfessor, MessageController.analyzeMessage);

// 메시지 초안 생성 (교수용)
router.post('/draft', authenticateToken, requireProfessor, MessageController.createDraft);

// 메시지 전송 (교수용)
router.post('/:messageId/send', authenticateToken, requireProfessor, MessageController.sendMessage);

// 보낸 메시지 목록 조회 (교수용)
router.get('/sent', authenticateToken, requireProfessor, MessageController.getSentMessages);

// 받은 메시지 목록 조회 (학생용)
router.get('/received', authenticateToken, requireStudent, MessageController.getReceivedMessages);

// 메시지 읽음 표시 (학생용)
router.put('/:messageId/read', authenticateToken, requireStudent, MessageController.markAsRead);

// 메시지 반응 추가 (학생용)
router.post('/:messageId/reaction', authenticateToken, requireStudent, MessageController.addReaction);

export default router;
