import { PrismaClient } from '@prisma/client';
import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';

const prisma = new PrismaClient();

/**
 * 사용자 등록
 */
export const register = async (req, res) => {
  try {
    const { email, password, name, role = 'VIEWER' } = req.body;

    // 이메일 중복 확인
    const existingUser = await prisma.user.findUnique({
      where: { email }
    });

    if (existingUser) {
      return res.status(400).json({
        success: false,
        error: '이미 등록된 이메일입니다.'
      });
    }

    // 비밀번호 해싱
    const hashedPassword = await bcrypt.hash(password, 10);

    // 사용자 생성
    const user = await prisma.user.create({
      data: {
        email,
        password: hashedPassword,
        name,
        role
      },
      select: {
        id: true,
        email: true,
        name: true,
        role: true,
        createdAt: true
      }
    });

    // JWT 토큰 생성
    const token = jwt.sign(
      { id: user.id, email: user.email, role: user.role },
      process.env.JWT_SECRET,
      { expiresIn: process.env.JWT_EXPIRES_IN || '7d' }
    );

    res.status(201).json({
      success: true,
      message: '사용자 등록이 완료되었습니다.',
      data: {
        user,
        token
      }
    });
  } catch (error) {
    console.error('사용자 등록 오류:', error);
    res.status(500).json({
      success: false,
      error: '사용자 등록 중 오류가 발생했습니다.',
      details: error.message
    });
  }
};

/**
 * 로그인
 */
export const login = async (req, res) => {
  try {
    const { email, password } = req.body;

    // 사용자 조회
    const user = await prisma.user.findUnique({
      where: { email }
    });

    if (!user) {
      return res.status(401).json({
        success: false,
        error: '이메일 또는 비밀번호가 올바르지 않습니다.'
      });
    }

    // 비밀번호 확인
    const isPasswordValid = await bcrypt.compare(password, user.password);

    if (!isPasswordValid) {
      return res.status(401).json({
        success: false,
        error: '이메일 또는 비밀번호가 올바르지 않습니다.'
      });
    }

    // 마지막 로그인 시간 업데이트
    await prisma.user.update({
      where: { id: user.id },
      data: { lastLoginAt: new Date() }
    });

    // JWT 토큰 생성
    const token = jwt.sign(
      { id: user.id, email: user.email, role: user.role },
      process.env.JWT_SECRET,
      { expiresIn: process.env.JWT_EXPIRES_IN || '7d' }
    );

    res.json({
      success: true,
      message: '로그인에 성공했습니다.',
      data: {
        user: {
          id: user.id,
          email: user.email,
          name: user.name,
          role: user.role,
          createdAt: user.createdAt
        },
        token
      }
    });
  } catch (error) {
    console.error('로그인 오류:', error);
    res.status(500).json({
      success: false,
      error: '로그인 중 오류가 발생했습니다.',
      details: error.message
    });
  }
};

/**
 * 프로필 조회
 */
export const getProfile = async (req, res) => {
  try {
    const user = await prisma.user.findUnique({
      where: { id: req.user.id },
      select: {
        id: true,
        email: true,
        name: true,
        role: true,
        createdAt: true,
        lastLoginAt: true,
        _count: {
          select: {
            textbooks: true,
            workflowSteps: true,
            comments: true
          }
        }
      }
    });

    if (!user) {
      return res.status(404).json({
        success: false,
        error: '사용자를 찾을 수 없습니다.'
      });
    }

    res.json({
      success: true,
      data: user
    });
  } catch (error) {
    console.error('프로필 조회 오류:', error);
    res.status(500).json({
      success: false,
      error: '프로필 조회 중 오류가 발생했습니다.',
      details: error.message
    });
  }
};

/**
 * 프로필 업데이트
 */
export const updateProfile = async (req, res) => {
  try {
    const { name, currentPassword, newPassword } = req.body;
    const updateData = {};

    // 이름 업데이트
    if (name) {
      updateData.name = name;
    }

    // 비밀번호 변경
    if (currentPassword && newPassword) {
      const user = await prisma.user.findUnique({
        where: { id: req.user.id }
      });

      const isPasswordValid = await bcrypt.compare(currentPassword, user.password);

      if (!isPasswordValid) {
        return res.status(400).json({
          success: false,
          error: '현재 비밀번호가 올바르지 않습니다.'
        });
      }

      updateData.password = await bcrypt.hash(newPassword, 10);
    }

    const updatedUser = await prisma.user.update({
      where: { id: req.user.id },
      data: updateData,
      select: {
        id: true,
        email: true,
        name: true,
        role: true,
        createdAt: true,
        lastLoginAt: true
      }
    });

    res.json({
      success: true,
      message: '프로필이 성공적으로 업데이트되었습니다.',
      data: updatedUser
    });
  } catch (error) {
    console.error('프로필 업데이트 오류:', error);
    res.status(500).json({
      success: false,
      error: '프로필 업데이트 중 오류가 발생했습니다.',
      details: error.message
    });
  }
};

/**
 * 모든 사용자 조회 (관리자 전용)
 */
export const getAllUsers = async (req, res) => {
  try {
    const { page = 1, limit = 10, role, search } = req.query;
    const skip = (page - 1) * limit;
    const where = {};

    if (role) where.role = role;
    if (search) {
      where.OR = [
        { name: { contains: search, mode: 'insensitive' } },
        { email: { contains: search, mode: 'insensitive' } }
      ];
    }

    const [users, total] = await Promise.all([
      prisma.user.findMany({
        where,
        skip: parseInt(skip),
        take: parseInt(limit),
        select: {
          id: true,
          email: true,
          name: true,
          role: true,
          createdAt: true,
          lastLoginAt: true,
          _count: {
            select: {
              textbooks: true,
              workflowSteps: true,
              comments: true
            }
          }
        },
        orderBy: {
          createdAt: 'desc'
        }
      }),
      prisma.user.count({ where })
    ]);

    res.json({
      success: true,
      data: users,
      pagination: {
        page: parseInt(page),
        limit: parseInt(limit),
        total,
        totalPages: Math.ceil(total / limit)
      }
    });
  } catch (error) {
    console.error('사용자 조회 오류:', error);
    res.status(500).json({
      success: false,
      error: '사용자 조회 중 오류가 발생했습니다.',
      details: error.message
    });
  }
};

/**
 * 사용자 역할 업데이트 (관리자 전용)
 */
export const updateUserRole = async (req, res) => {
  try {
    const { userId } = req.params;
    const { role } = req.body;

    const user = await prisma.user.update({
      where: { id: userId },
      data: { role },
      select: {
        id: true,
        email: true,
        name: true,
        role: true
      }
    });

    res.json({
      success: true,
      message: '사용자 역할이 성공적으로 업데이트되었습니다.',
      data: user
    });
  } catch (error) {
    console.error('사용자 역할 업데이트 오류:', error);
    res.status(500).json({
      success: false,
      error: '사용자 역할 업데이트 중 오류가 발생했습니다.',
      details: error.message
    });
  }
};

/**
 * 사용자 삭제 (관리자 전용)
 */
export const deleteUser = async (req, res) => {
  try {
    const { userId } = req.params;

    // 자기 자신은 삭제할 수 없음
    if (userId === req.user.id) {
      return res.status(400).json({
        success: false,
        error: '자기 자신을 삭제할 수 없습니다.'
      });
    }

    await prisma.user.delete({
      where: { id: userId }
    });

    res.json({
      success: true,
      message: '사용자가 성공적으로 삭제되었습니다.'
    });
  } catch (error) {
    console.error('사용자 삭제 오류:', error);
    res.status(500).json({
      success: false,
      error: '사용자 삭제 중 오류가 발생했습니다.',
      details: error.message
    });
  }
};
