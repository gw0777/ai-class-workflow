import express from 'express';
import { GroupController } from '../controllers/groupController.js';
import { authenticateToken, requireProfessor } from '../middleware/auth.js';

const router = express.Router();

// 그룹 생성
router.post('/', authenticateToken, requireProfessor, GroupController.createGroup);

// 그룹 목록 조회
router.get('/', authenticateToken, requireProfessor, GroupController.getGroups);

// 그룹 상세 정보 조회
router.get('/:groupId', authenticateToken, requireProfessor, GroupController.getGroupDetails);

// 그룹에 학생 추가
router.post('/:groupId/students', authenticateToken, requireProfessor, GroupController.addStudents);

// 그룹에서 학생 제거
router.delete('/:groupId/students/:studentId', authenticateToken, requireProfessor, GroupController.removeStudent);

// 그룹 삭제
router.delete('/:groupId', authenticateToken, requireProfessor, GroupController.deleteGroup);

export default router;
