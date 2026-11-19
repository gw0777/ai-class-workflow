import db from '../models/database.js';

export class GroupController {
  /**
   * 그룹 생성
   */
  static createGroup(req, res) {
    try {
      const { name, description, studentIds } = req.body;
      const professorId = req.user.userId;

      if (!name) {
        return res.status(400).json({ error: '그룹 이름이 필요합니다.' });
      }

      // 그룹 생성
      const insertGroup = db.prepare(`
        INSERT INTO groups (name, description, professor_id)
        VALUES (?, ?, ?)
      `);

      const result = insertGroup.run(name, description || null, professorId);
      const groupId = result.lastInsertRowid;

      // 학생 추가
      if (studentIds && studentIds.length > 0) {
        const insertMember = db.prepare(`
          INSERT INTO group_members (group_id, student_id)
          VALUES (?, ?)
        `);

        for (const studentId of studentIds) {
          insertMember.run(groupId, studentId);
        }
      }

      res.status(201).json({
        message: '그룹이 생성되었습니다.',
        groupId
      });
    } catch (error) {
      console.error('Create group error:', error);
      res.status(500).json({ error: '그룹 생성 중 오류가 발생했습니다.' });
    }
  }

  /**
   * 교수의 그룹 목록 조회
   */
  static getGroups(req, res) {
    try {
      const professorId = req.user.userId;

      const groups = db.prepare(`
        SELECT
          g.*,
          COUNT(gm.id) as member_count
        FROM groups g
        LEFT JOIN group_members gm ON g.id = gm.group_id
        WHERE g.professor_id = ?
        GROUP BY g.id
        ORDER BY g.created_at DESC
      `).all(professorId);

      res.json({ groups });
    } catch (error) {
      console.error('Get groups error:', error);
      res.status(500).json({ error: '그룹 조회 중 오류가 발생했습니다.' });
    }
  }

  /**
   * 그룹 상세 정보 및 멤버 조회
   */
  static getGroupDetails(req, res) {
    try {
      const { groupId } = req.params;
      const professorId = req.user.userId;

      // 그룹 정보 조회
      const group = db.prepare(`
        SELECT * FROM groups
        WHERE id = ? AND professor_id = ?
      `).get(groupId, professorId);

      if (!group) {
        return res.status(404).json({ error: '그룹을 찾을 수 없습니다.' });
      }

      // 그룹 멤버 조회
      const members = db.prepare(`
        SELECT
          u.id,
          u.name,
          u.email,
          u.student_id as studentId,
          gm.joined_at as joinedAt
        FROM group_members gm
        JOIN users u ON gm.student_id = u.id
        WHERE gm.group_id = ?
        ORDER BY u.name
      `).all(groupId);

      res.json({
        group,
        members
      });
    } catch (error) {
      console.error('Get group details error:', error);
      res.status(500).json({ error: '그룹 정보 조회 중 오류가 발생했습니다.' });
    }
  }

  /**
   * 그룹에 학생 추가
   */
  static addStudents(req, res) {
    try {
      const { groupId } = req.params;
      const { studentIds } = req.body;
      const professorId = req.user.userId;

      // 그룹 소유권 확인
      const group = db.prepare(`
        SELECT id FROM groups WHERE id = ? AND professor_id = ?
      `).get(groupId, professorId);

      if (!group) {
        return res.status(404).json({ error: '그룹을 찾을 수 없습니다.' });
      }

      if (!studentIds || studentIds.length === 0) {
        return res.status(400).json({ error: '추가할 학생을 선택해주세요.' });
      }

      // 학생 추가 (중복 무시)
      const insertMember = db.prepare(`
        INSERT OR IGNORE INTO group_members (group_id, student_id)
        VALUES (?, ?)
      `);

      let addedCount = 0;
      for (const studentId of studentIds) {
        const result = insertMember.run(groupId, studentId);
        if (result.changes > 0) addedCount++;
      }

      res.json({
        message: `${addedCount}명의 학생이 그룹에 추가되었습니다.`,
        addedCount
      });
    } catch (error) {
      console.error('Add students error:', error);
      res.status(500).json({ error: '학생 추가 중 오류가 발생했습니다.' });
    }
  }

  /**
   * 그룹에서 학생 제거
   */
  static removeStudent(req, res) {
    try {
      const { groupId, studentId } = req.params;
      const professorId = req.user.userId;

      // 그룹 소유권 확인
      const group = db.prepare(`
        SELECT id FROM groups WHERE id = ? AND professor_id = ?
      `).get(groupId, professorId);

      if (!group) {
        return res.status(404).json({ error: '그룹을 찾을 수 없습니다.' });
      }

      // 학생 제거
      const deleteStmt = db.prepare(`
        DELETE FROM group_members
        WHERE group_id = ? AND student_id = ?
      `);

      deleteStmt.run(groupId, studentId);

      res.json({ message: '학생이 그룹에서 제거되었습니다.' });
    } catch (error) {
      console.error('Remove student error:', error);
      res.status(500).json({ error: '학생 제거 중 오류가 발생했습니다.' });
    }
  }

  /**
   * 그룹 삭제
   */
  static deleteGroup(req, res) {
    try {
      const { groupId } = req.params;
      const professorId = req.user.userId;

      const deleteStmt = db.prepare(`
        DELETE FROM groups
        WHERE id = ? AND professor_id = ?
      `);

      const result = deleteStmt.run(groupId, professorId);

      if (result.changes === 0) {
        return res.status(404).json({ error: '그룹을 찾을 수 없습니다.' });
      }

      res.json({ message: '그룹이 삭제되었습니다.' });
    } catch (error) {
      console.error('Delete group error:', error);
      res.status(500).json({ error: '그룹 삭제 중 오류가 발생했습니다.' });
    }
  }
}
