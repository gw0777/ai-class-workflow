import express from 'express';
import { AuthController } from '../controllers/authController.js';
import { authenticateToken } from '../middleware/auth.js';

const router = express.Router();

// 회원가입
router.post('/register', AuthController.register);

// 로그인
router.post('/login', AuthController.login);

// 현재 사용자 정보 조회
router.get('/me', authenticateToken, AuthController.getCurrentUser);

export default router;
