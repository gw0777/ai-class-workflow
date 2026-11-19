import React, { useState, useEffect } from 'react';
import Header from '../components/Header';
import { messageAPI } from '../services/api';

function StudentDashboard() {
  const [messages, setMessages] = useState([]);
  const [selectedMessage, setSelectedMessage] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadMessages();
  }, []);

  const loadMessages = async () => {
    try {
      const response = await messageAPI.getReceivedMessages();
      setMessages(response.data.messages);
    } catch (err) {
      setError('메시지를 불러오는 중 오류가 발생했습니다.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleMessageClick = async (message) => {
    setSelectedMessage(message);

    // 읽지 않은 메시지면 읽음 표시
    if (!message.isRead) {
      try {
        await messageAPI.markAsRead(message.id);
        // 로컬 상태 업데이트
        setMessages((prev) =>
          prev.map((m) =>
            m.id === message.id ? { ...m, isRead: 1 } : m
          )
        );
      } catch (err) {
        console.error('Failed to mark as read:', err);
      }
    }
  };

  const handleReaction = async (messageId, reaction) => {
    try {
      await messageAPI.addReaction(messageId, reaction);
      alert('반응이 등록되었습니다.');
    } catch (err) {
      alert('반응 등록에 실패했습니다.');
      console.error(err);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString('ko-KR');
  };

  const unreadCount = messages.filter((m) => !m.isRead).length;

  return (
    <div>
      <Header />
      <div className="container">
        <h1 className="mb-20">학생 대시보드</h1>

        <div className="card mb-20">
          <h3>알림</h3>
          <p style={{ fontSize: '24px', fontWeight: 'bold', color: '#4CAF50' }}>
            {unreadCount}개의 읽지 않은 메시지
          </p>
        </div>

        <div className="grid" style={{ gridTemplateColumns: '1fr 2fr', gap: '20px' }}>
          {/* 메시지 목록 */}
          <div className="card">
            <h2 className="mb-20">받은 메시지</h2>

            {loading && (
              <div className="loading">
                <div className="spinner"></div>
              </div>
            )}

            {error && <div className="alert alert-danger">{error}</div>}

            {!loading && !error && messages.length === 0 && (
              <p className="text-center" style={{ padding: '20px', color: '#666' }}>
                받은 메시지가 없습니다.
              </p>
            )}

            {!loading && !error && messages.length > 0 && (
              <ul className="message-list">
                {messages.map((message) => (
                  <li
                    key={message.id}
                    className={`message-item ${!message.isRead ? 'unread' : ''}`}
                    onClick={() => handleMessageClick(message)}
                    style={{ cursor: 'pointer' }}
                  >
                    <div style={{ fontWeight: message.isRead ? 'normal' : 'bold' }}>
                      {message.professorName}
                    </div>
                    <div style={{ fontSize: '12px', color: '#666' }}>
                      {message.department}
                    </div>
                    <div style={{ fontSize: '12px', color: '#999', marginTop: '5px' }}>
                      {formatDate(message.sentAt)}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* 메시지 내용 */}
          <div className="card">
            {selectedMessage ? (
              <>
                <div className="mb-20">
                  <h2>{selectedMessage.professorName}</h2>
                  <p style={{ color: '#666' }}>
                    {selectedMessage.department} | {formatDate(selectedMessage.sentAt)}
                  </p>
                </div>

                <div
                  style={{
                    background: '#f5f5f5',
                    padding: '20px',
                    borderRadius: '5px',
                    whiteSpace: 'pre-wrap',
                    marginBottom: '20px',
                  }}
                >
                  {selectedMessage.content}
                </div>

                <div>
                  <h3 className="mb-20">이 메시지가 도움이 되었나요?</h3>
                  <div className="flex gap-10">
                    <button
                      className="btn btn-primary"
                      onClick={() => handleReaction(selectedMessage.id, 'helpful')}
                    >
                      도움됨
                    </button>
                    <button
                      className="btn btn-secondary"
                      onClick={() => handleReaction(selectedMessage.id, 'clear')}
                    >
                      명확함
                    </button>
                    <button
                      className="btn btn-outline"
                      onClick={() => handleReaction(selectedMessage.id, 'confusing')}
                    >
                      혼란스러움
                    </button>
                  </div>
                </div>
              </>
            ) : (
              <div
                className="flex-center"
                style={{ height: '100%', color: '#999' }}
              >
                메시지를 선택하세요
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default StudentDashboard;
