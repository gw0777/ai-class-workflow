import express from 'express';
import { UserController } from '../controllers/userController.js';
import { authenticateToken, requireProfessor } from '../middleware/auth.js';

const router = express.Router();

// 학생 목록 조회
router.get('/students', authenticateToken, requireProfessor, UserController.getStudents);

// 학생 검색
router.get('/students/search', authenticateToken, requireProfessor, UserController.searchStudents);

// 특정 학생 정보 조회
router.get('/students/:studentId', authenticateToken, requireProfessor, UserController.getStudent);

export default router;
