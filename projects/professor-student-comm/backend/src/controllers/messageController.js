import db from '../models/database.js';
import AIMessageService from '../services/aiService.js';

export class MessageController {
  /**
   * 메시지 AI 분석 (전송 전)
   */
  static async analyzeMessage(req, res) {
    try {
      const { content, isGroupMessage, recipientIds, groupId } = req.body;

      if (!content) {
        return res.status(400).json({ error: '메시지 내용이 필요합니다.' });
      }

      // AI 분석 수행
      const analysis = await AIMessageService.analyzeMessage(content, isGroupMessage);

      if (!analysis.success) {
        return res.status(500).json({
          error: 'AI 분석 실패',
          details: analysis.error
        });
      }

      // 분석 결과만 반환 (아직 저장하지 않음)
      res.json({
        message: '메시지 분석 완료',
        originalContent: content,
        analysis: analysis.analysis
      });
    } catch (error) {
      console.error('Message analysis error:', error);
      res.status(500).json({ error: '메시지 분석 중 오류가 발생했습니다.' });
    }
  }

  /**
   * 메시지 생성 및 저장 (draft 상태)
   */
  static async createDraft(req, res) {
    try {
      const {
        originalContent,
        aiAnalyzedContent,
        aiSuggestions,
        finalContent,
        emotionAnalysis,
        riskLevel,
        isGroupMessage,
        recipientIds,
        groupId
      } = req.body;

      const professorId = req.user.userId;

      // 트랜잭션 시작
      const insertMessage = db.prepare(`
        INSERT INTO messages (
          professor_id, original_content, ai_analyzed_content,
          ai_suggestions, final_content, emotion_analysis,
          risk_level, is_group_message, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'draft')
      `);

      const result = insertMessage.run(
        professorId,
        originalContent,
        JSON.stringify(aiAnalyzedContent),
        JSON.stringify(aiSuggestions),
        finalContent,
        emotionAnalysis,
        riskLevel,
        isGroupMessage ? 1 : 0
      );

      const messageId = result.lastInsertRowid;

      // 수신자 추가
      if (isGroupMessage && groupId) {
        const insertRecipient = db.prepare(`
          INSERT INTO message_recipients (message_id, group_id)
          VALUES (?, ?)
        `);
        insertRecipient.run(messageId, groupId);
      } else if (recipientIds && recipientIds.length > 0) {
        const insertRecipient = db.prepare(`
          INSERT INTO message_recipients (message_id, recipient_id)
          VALUES (?, ?)
        `);

        for (const recipientId of recipientIds) {
          insertRecipient.run(messageId, recipientId);
        }
      }

      res.status(201).json({
        message: '메시지 초안이 저장되었습니다.',
        messageId
      });
    } catch (error) {
      console.error('Create draft error:', error);
      res.status(500).json({ error: '메시지 저장 중 오류가 발생했습니다.' });
    }
  }

  /**
   * 메시지 승인 및 전송
   */
  static async sendMessage(req, res) {
    try {
      const { messageId } = req.params;
      const { finalContent } = req.body; // 교수가 최종 수정한 내용
      const professorId = req.user.userId;

      // 메시지 조회 및 권한 확인
      const message = db.prepare(`
        SELECT * FROM messages
        WHERE id = ? AND professor_id = ? AND status = 'draft'
      `).get(messageId, professorId);

      if (!message) {
        return res.status(404).json({ error: '메시지를 찾을 수 없거나 이미 전송되었습니다.' });
      }

      // 메시지 상태 업데이트
      const updateStmt = db.prepare(`
        UPDATE messages
        SET final_content = ?, status = 'sent', sent_at = CURRENT_TIMESTAMP
        WHERE id = ?
      `);

      updateStmt.run(finalContent || message.final_content, messageId);

      res.json({
        message: '메시지가 전송되었습니다.',
        messageId
      });
    } catch (error) {
      console.error('Send message error:', error);
      res.status(500).json({ error: '메시지 전송 중 오류가 발생했습니다.' });
    }
  }

  /**
   * 교수가 보낸 메시지 목록 조회
   */
  static getSentMessages(req, res) {
    try {
      const professorId = req.user.userId;

      const messages = db.prepare(`
        SELECT
          m.*,
          GROUP_CONCAT(DISTINCT u.name) as recipients
        FROM messages m
        LEFT JOIN message_recipients mr ON m.id = mr.message_id
        LEFT JOIN users u ON mr.recipient_id = u.id
        WHERE m.professor_id = ? AND m.status = 'sent'
        GROUP BY m.id
        ORDER BY m.sent_at DESC
      `).all(professorId);

      res.json({ messages });
    } catch (error) {
      console.error('Get sent messages error:', error);
      res.status(500).json({ error: '메시지 조회 중 오류가 발생했습니다.' });
    }
  }

  /**
   * 학생이 받은 메시지 조회
   */
  static getReceivedMessages(req, res) {
    try {
      const studentId = req.user.userId;

      const messages = db.prepare(`
        SELECT
          m.id,
          m.final_content as content,
          m.sent_at as sentAt,
          u.name as professorName,
          u.department,
          mr.is_read as isRead,
          mr.read_at as readAt
        FROM messages m
        JOIN message_recipients mr ON m.id = mr.message_id
        JOIN users u ON m.professor_id = u.id
        WHERE mr.recipient_id = ? AND m.status = 'sent'
        ORDER BY m.sent_at DESC
      `).all(studentId);

      res.json({ messages });
    } catch (error) {
      console.error('Get received messages error:', error);
      res.status(500).json({ error: '메시지 조회 중 오류가 발생했습니다.' });
    }
  }

  /**
   * 메시지 읽음 표시
   */
  static markAsRead(req, res) {
    try {
      const { messageId } = req.params;
      const studentId = req.user.userId;

      const updateStmt = db.prepare(`
        UPDATE message_recipients
        SET is_read = 1, read_at = CURRENT_TIMESTAMP
        WHERE message_id = ? AND recipient_id = ?
      `);

      updateStmt.run(messageId, studentId);

      res.json({ message: '메시지를 읽음으로 표시했습니다.' });
    } catch (error) {
      console.error('Mark as read error:', error);
      res.status(500).json({ error: '메시지 업데이트 중 오류가 발생했습니다.' });
    }
  }

  /**
   * 메시지에 반응 추가
   */
  static addReaction(req, res) {
    try {
      const { messageId } = req.params;
      const { reaction } = req.body;
      const studentId = req.user.userId;

      if (!['helpful', 'clear', 'confusing'].includes(reaction)) {
        return res.status(400).json({ error: '유효하지 않은 반응입니다.' });
      }

      const stmt = db.prepare(`
        INSERT OR REPLACE INTO message_reactions (message_id, student_id, reaction)
        VALUES (?, ?, ?)
      `);

      stmt.run(messageId, studentId, reaction);

      res.json({ message: '반응이 등록되었습니다.' });
    } catch (error) {
      console.error('Add reaction error:', error);
      res.status(500).json({ error: '반응 등록 중 오류가 발생했습니다.' });
    }
  }
}
