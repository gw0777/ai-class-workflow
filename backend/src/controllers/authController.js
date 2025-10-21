import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';
import db from '../models/database.js';

export class AuthController {
  /**
   * 사용자 회원가입
   */
  static register(req, res) {
    try {
      const { email, password, name, role, department, studentId } = req.body;

      // 입력 검증
      if (!email || !password || !name || !role) {
        return res.status(400).json({ error: '필수 정보가 누락되었습니다.' });
      }

      if (!['professor', 'student'].includes(role)) {
        return res.status(400).json({ error: '유효하지 않은 역할입니다.' });
      }

      // 이메일 중복 확인
      const existingUser = db.prepare('SELECT id FROM users WHERE email = ?').get(email);
      if (existingUser) {
        return res.status(400).json({ error: '이미 사용 중인 이메일입니다.' });
      }

      // 비밀번호 해싱
      const hashedPassword = bcrypt.hashSync(password, 10);

      // 사용자 생성
      const stmt = db.prepare(`
        INSERT INTO users (email, password, name, role, department, student_id)
        VALUES (?, ?, ?, ?, ?, ?)
      `);

      const result = stmt.run(
        email,
        hashedPassword,
        name,
        role,
        department || null,
        studentId || null
      );

      res.status(201).json({
        message: '회원가입이 완료되었습니다.',
        userId: result.lastInsertRowid
      });
    } catch (error) {
      console.error('Registration error:', error);
      res.status(500).json({ error: '회원가입 중 오류가 발생했습니다.' });
    }
  }

  /**
   * 사용자 로그인
   */
  static login(req, res) {
    try {
      const { email, password } = req.body;

      if (!email || !password) {
        return res.status(400).json({ error: '이메일과 비밀번호를 입력해주세요.' });
      }

      // 사용자 조회
      const user = db.prepare('SELECT * FROM users WHERE email = ?').get(email);

      if (!user) {
        return res.status(401).json({ error: '이메일 또는 비밀번호가 올바르지 않습니다.' });
      }

      // 비밀번호 확인
      const isValidPassword = bcrypt.compareSync(password, user.password);

      if (!isValidPassword) {
        return res.status(401).json({ error: '이메일 또는 비밀번호가 올바르지 않습니다.' });
      }

      // JWT 토큰 생성
      const token = jwt.sign(
        {
          userId: user.id,
          email: user.email,
          role: user.role,
          name: user.name
        },
        process.env.JWT_SECRET,
        { expiresIn: '7d' }
      );

      res.json({
        message: '로그인 성공',
        token,
        user: {
          id: user.id,
          email: user.email,
          name: user.name,
          role: user.role,
          department: user.department
        }
      });
    } catch (error) {
      console.error('Login error:', error);
      res.status(500).json({ error: '로그인 중 오류가 발생했습니다.' });
    }
  }

  /**
   * 현재 사용자 정보 조회
   */
  static getCurrentUser(req, res) {
    try {
      const user = db.prepare(`
        SELECT id, email, name, role, department, student_id as studentId, created_at as createdAt
        FROM users WHERE id = ?
      `).get(req.user.userId);

      if (!user) {
        return res.status(404).json({ error: '사용자를 찾을 수 없습니다.' });
      }

      res.json({ user });
    } catch (error) {
      console.error('Get user error:', error);
      res.status(500).json({ error: '사용자 정보 조회 중 오류가 발생했습니다.' });
    }
  }
}
