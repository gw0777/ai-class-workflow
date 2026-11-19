import express from 'express';
import {
  register,
  login,
  getProfile,
  updateProfile,
  getAllUsers,
  updateUserRole,
  deleteUser
} from '../controllers/user.controller.js';
import { authenticate, authorize } from '../middleware/auth.middleware.js';
import { validateUser, validateLogin } from '../middleware/validation.middleware.js';

const router = express.Router();

// 인증 라우트
router.post('/register', validateUser, register);
router.post('/login', validateLogin, login);

// 프로필 관리 (인증 필요)
router.get('/profile', authenticate, getProfile);
router.put('/profile', authenticate, updateProfile);

// 사용자 관리 (관리자 전용)
router.get('/', authenticate, authorize(['ADMIN']), getAllUsers);
router.put('/:userId/role', authenticate, authorize(['ADMIN']), updateUserRole);
router.delete('/:userId', authenticate, authorize(['ADMIN']), deleteUser);

export default router;
