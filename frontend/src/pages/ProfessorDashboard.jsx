import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Header from '../components/Header';
import { messageAPI } from '../services/api';

function ProfessorDashboard() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadMessages();
  }, []);

  const loadMessages = async () => {
    try {
      const response = await messageAPI.getSentMessages();
      setMessages(response.data.messages);
    } catch (err) {
      setError('메시지를 불러오는 중 오류가 발생했습니다.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString('ko-KR');
  };

  return (
    <div>
      <Header />
      <div className="container">
        <div className="flex-between mb-20">
          <h1>교수 대시보드</h1>
          <Link to="/professor/compose" className="btn btn-primary">
            새 메시지 작성
          </Link>
        </div>

        <div className="grid grid-2 mb-20">
          <div className="card">
            <h3>빠른 통계</h3>
            <p style={{ fontSize: '32px', fontWeight: 'bold', color: '#4CAF50' }}>
              {messages.length}
            </p>
            <p>전송한 메시지</p>
          </div>

          <div className="card">
            <h3>빠른 작업</h3>
            <div className="flex gap-10" style={{ flexDirection: 'column' }}>
              <Link to="/professor/compose" className="btn btn-secondary">
                메시지 작성
              </Link>
              <Link to="/professor/groups" className="btn btn-outline">
                그룹 관리
              </Link>
            </div>
          </div>
        </div>

        <div className="card">
          <h2 className="mb-20">전송한 메시지 목록</h2>

          {loading && (
            <div className="loading">
              <div className="spinner"></div>
            </div>
          )}

          {error && <div className="alert alert-danger">{error}</div>}

          {!loading && !error && messages.length === 0 && (
            <p className="text-center" style={{ padding: '40px', color: '#666' }}>
              아직 전송한 메시지가 없습니다.
            </p>
          )}

          {!loading && !error && messages.length > 0 && (
            <ul className="message-list">
              {messages.map((message) => (
                <li key={message.id} className="message-item">
                  <div className="flex-between">
                    <div>
                      <div style={{ fontWeight: '500', marginBottom: '5px' }}>
                        수신자: {message.recipients || '알 수 없음'}
                      </div>
                      <div
                        style={{
                          color: '#666',
                          fontSize: '14px',
                          marginBottom: '10px',
                        }}
                      >
                        {message.final_content.substring(0, 100)}
                        {message.final_content.length > 100 && '...'}
                      </div>
                      <div style={{ fontSize: '12px', color: '#999' }}>
                        전송일: {formatDate(message.sent_at)}
                      </div>
                    </div>
                    <div>
                      <span
                        className={`risk-level risk-${message.risk_level || 'low'}`}
                      >
                        {message.risk_level === 'low'
                          ? '낮음'
                          : message.risk_level === 'medium'
                          ? '보통'
                          : message.risk_level === 'high'
                          ? '높음'
                          : 'N/A'}
                      </span>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}

export default ProfessorDashboard;
