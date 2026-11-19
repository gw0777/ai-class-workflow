import db from '../models/database.js';

export class UserController {
  /**
   * 학생 목록 조회 (교수용)
   */
  static getStudents(req, res) {
    try {
      const students = db.prepare(`
        SELECT id, name, email, student_id as studentId, department
        FROM users
        WHERE role = 'student'
        ORDER BY name
      `).all();

      res.json({ students });
    } catch (error) {
      console.error('Get students error:', error);
      res.status(500).json({ error: '학생 목록 조회 중 오류가 발생했습니다.' });
    }
  }

  /**
   * 특정 학생 정보 조회
   */
  static getStudent(req, res) {
    try {
      const { studentId } = req.params;

      const student = db.prepare(`
        SELECT id, name, email, student_id as studentId, department, created_at as createdAt
        FROM users
        WHERE id = ? AND role = 'student'
      `).get(studentId);

      if (!student) {
        return res.status(404).json({ error: '학생을 찾을 수 없습니다.' });
      }

      res.json({ student });
    } catch (error) {
      console.error('Get student error:', error);
      res.status(500).json({ error: '학생 정보 조회 중 오류가 발생했습니다.' });
    }
  }

  /**
   * 학생 검색
   */
  static searchStudents(req, res) {
    try {
      const { query } = req.query;

      if (!query) {
        return res.status(400).json({ error: '검색어를 입력해주세요.' });
      }

      const students = db.prepare(`
        SELECT id, name, email, student_id as studentId, department
        FROM users
        WHERE role = 'student'
          AND (name LIKE ? OR email LIKE ? OR student_id LIKE ?)
        ORDER BY name
        LIMIT 50
      `).all(`%${query}%`, `%${query}%`, `%${query}%`);

      res.json({ students });
    } catch (error) {
      console.error('Search students error:', error);
      res.status(500).json({ error: '학생 검색 중 오류가 발생했습니다.' });
    }
  }
}
