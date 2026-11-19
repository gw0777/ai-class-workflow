import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import { messageAPI, userAPI, groupAPI } from '../services/api';

function ComposeMessage() {
  const [step, setStep] = useState(1); // 1: 수신자 선택, 2: 메시지 작성, 3: AI 분석, 4: 최종 확인
  const [messageType, setMessageType] = useState('individual'); // individual or group
  const [selectedStudents, setSelectedStudents] = useState([]);
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [students, setStudents] = useState([]);
  const [groups, setGroups] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');

  const [originalMessage, setOriginalMessage] = useState('');
  const [aiAnalysis, setAiAnalysis] = useState(null);
  const [finalMessage, setFinalMessage] = useState('');
  const [analyzing, setAnalyzing] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');

  const navigate = useNavigate();

  useEffect(() => {
    loadStudents();
    loadGroups();
  }, []);

  const loadStudents = async () => {
    try {
      const response = await userAPI.getStudents();
      setStudents(response.data.students);
    } catch (err) {
      console.error('Failed to load students:', err);
    }
  };

  const loadGroups = async () => {
    try {
      const response = await groupAPI.getGroups();
      setGroups(response.data.groups);
    } catch (err) {
      console.error('Failed to load groups:', err);
    }
  };

  const handleStudentToggle = (studentId) => {
    setSelectedStudents((prev) =>
      prev.includes(studentId)
        ? prev.filter((id) => id !== studentId)
        : [...prev, studentId]
    );
  };

  const handleAnalyze = async () => {
    if (!originalMessage.trim()) {
      setError('메시지를 입력해주세요.');
      return;
    }

    setAnalyzing(true);
    setError('');

    try {
      const response = await messageAPI.analyzeMessage({
        content: originalMessage,
        isGroupMessage: messageType === 'group',
        recipientIds: messageType === 'individual' ? selectedStudents : null,
        groupId: messageType === 'group' ? selectedGroup : null,
      });

      setAiAnalysis(response.data.analysis);
      setFinalMessage(response.data.analysis.improvedMessage);
      setStep(3);
    } catch (err) {
      setError('AI 분석 중 오류가 발생했습니다: ' + err.response?.data?.error);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleSend = async () => {
    setSending(true);
    setError('');

    try {
      // 1. 초안 생성
      const draftResponse = await messageAPI.createDraft({
        originalContent: originalMessage,
        aiAnalyzedContent: aiAnalysis,
        aiSuggestions: aiAnalysis.suggestions,
        finalContent: finalMessage,
        emotionAnalysis: aiAnalysis.emotionAnalysis,
        riskLevel: aiAnalysis.riskLevel,
        isGroupMessage: messageType === 'group',
        recipientIds: messageType === 'individual' ? selectedStudents : null,
        groupId: messageType === 'group' ? selectedGroup : null,
      });

      const messageId = draftResponse.data.messageId;

      // 2. 메시지 전송
      await messageAPI.sendMessage(messageId, { finalContent });

      alert('메시지가 성공적으로 전송되었습니다!');
      navigate('/professor/dashboard');
    } catch (err) {
      setError('메시지 전송 중 오류가 발생했습니다: ' + err.response?.data?.error);
    } finally {
      setSending(false);
    }
  };

  const filteredStudents = students.filter(
    (s) =>
      s.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (s.studentId && s.studentId.includes(searchQuery))
  );

  return (
    <div>
      <Header />
      <div className="container">
        <h1 className="mb-20">메시지 작성</h1>

        {error && <div className="alert alert-danger">{error}</div>}

        {/* Step 1: 수신자 선택 */}
        {step === 1 && (
          <div className="card">
            <h2>1단계: 수신자 선택</h2>

            <div className="form-group">
              <label>메시지 유형</label>
              <select
                value={messageType}
                onChange={(e) => {
                  setMessageType(e.target.value);
                  setSelectedStudents([]);
                  setSelectedGroup(null);
                }}
              >
                <option value="individual">개별 학생</option>
                <option value="group">그룹</option>
              </select>
            </div>

            {messageType === 'individual' && (
              <>
                <div className="form-group">
                  <label>학생 검색</label>
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="이름, 이메일, 학번으로 검색"
                  />
                </div>

                <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
                  {filteredStudents.map((student) => (
                    <div
                      key={student.id}
                      style={{
                        padding: '10px',
                        borderBottom: '1px solid #eee',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '10px',
                      }}
                    >
                      <input
                        type="checkbox"
                        checked={selectedStudents.includes(student.id)}
                        onChange={() => handleStudentToggle(student.id)}
                      />
                      <div>
                        <div style={{ fontWeight: '500' }}>{student.name}</div>
                        <div style={{ fontSize: '12px', color: '#666' }}>
                          {student.email} {student.studentId && `(${student.studentId})`}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                <p className="mt-20">
                  <strong>{selectedStudents.length}</strong>명의 학생 선택됨
                </p>
              </>
            )}

            {messageType === 'group' && (
              <div className="form-group">
                <label>그룹 선택</label>
                <select
                  value={selectedGroup || ''}
                  onChange={(e) => setSelectedGroup(Number(e.target.value))}
                >
                  <option value="">그룹을 선택하세요</option>
                  {groups.map((group) => (
                    <option key={group.id} value={group.id}>
                      {group.name} ({group.member_count}명)
                    </option>
                  ))}
                </select>
              </div>
            )}

            <button
              className="btn btn-primary mt-20"
              onClick={() => setStep(2)}
              disabled={
                (messageType === 'individual' && selectedStudents.length === 0) ||
                (messageType === 'group' && !selectedGroup)
              }
            >
              다음 단계
            </button>
          </div>
        )}

        {/* Step 2: 메시지 작성 */}
        {step === 2 && (
          <div className="card">
            <h2>2단계: 메시지 작성</h2>

            <div className="alert alert-info">
              작성하신 메시지는 AI가 분석하여 감정적 표현을 제거하고, 오해의 소지를
              줄이는 방향으로 개선 제안을 드립니다.
            </div>

            <div className="form-group">
              <label>메시지 내용</label>
              <textarea
                value={originalMessage}
                onChange={(e) => setOriginalMessage(e.target.value)}
                placeholder="학생들에게 전달할 메시지를 자유롭게 작성하세요..."
                rows={10}
              />
            </div>

            <div className="flex gap-10">
              <button className="btn btn-outline" onClick={() => setStep(1)}>
                이전
              </button>
              <button
                className="btn btn-primary"
                onClick={handleAnalyze}
                disabled={analyzing || !originalMessage.trim()}
              >
                {analyzing ? 'AI 분석 중...' : 'AI 분석 시작'}
              </button>
            </div>
          </div>
        )}

        {/* Step 3: AI 분석 결과 */}
        {step === 3 && aiAnalysis && (
          <div className="card">
            <h2>3단계: AI 분석 결과</h2>

            <div className="ai-analysis">
              <h3>분석 결과</h3>

              <div className="mb-20">
                <strong>감정 분석:</strong> {aiAnalysis.emotionAnalysis}
              </div>

              <div className="mb-20">
                <strong>오해 위험도:</strong>{' '}
                <span className={`risk-level risk-${aiAnalysis.riskLevel}`}>
                  {aiAnalysis.riskLevel === 'low'
                    ? '낮음'
                    : aiAnalysis.riskLevel === 'medium'
                    ? '보통'
                    : '높음'}
                </span>
              </div>

              {aiAnalysis.issues && aiAnalysis.issues.length > 0 && (
                <div className="mb-20">
                  <strong>발견된 문제점:</strong>
                  <ul>
                    {aiAnalysis.issues.map((issue, index) => (
                      <li key={index}>{issue}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="mb-20">
                <strong>톤 평가:</strong> {aiAnalysis.toneAssessment}
              </div>

              {aiAnalysis.suggestions && aiAnalysis.suggestions.length > 0 && (
                <div className="mb-20">
                  <strong>개선 제안:</strong>
                  <ul>
                    {aiAnalysis.suggestions.map((suggestion, index) => (
                      <li key={index}>{suggestion}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            <div className="form-group mt-20">
              <label>
                <strong>원본 메시지:</strong>
              </label>
              <div
                style={{
                  background: '#f5f5f5',
                  padding: '15px',
                  borderRadius: '5px',
                  whiteSpace: 'pre-wrap',
                }}
              >
                {originalMessage}
              </div>
            </div>

            <div className="form-group">
              <label>
                <strong>AI 개선 메시지 (수정 가능):</strong>
              </label>
              <textarea
                value={finalMessage}
                onChange={(e) => setFinalMessage(e.target.value)}
                rows={10}
              />
            </div>

            <div className="flex gap-10">
              <button className="btn btn-outline" onClick={() => setStep(2)}>
                이전
              </button>
              <button className="btn btn-primary" onClick={() => setStep(4)}>
                다음 단계
              </button>
            </div>
          </div>
        )}

        {/* Step 4: 최종 확인 및 전송 */}
        {step === 4 && (
          <div className="card">
            <h2>4단계: 최종 확인</h2>

            <div className="alert alert-warning">
              메시지 전송 전 마지막으로 확인해주세요. 전송 후에는 수정할 수 없습니다.
            </div>

            <div className="mb-20">
              <strong>수신자:</strong>{' '}
              {messageType === 'individual'
                ? `${selectedStudents.length}명의 학생`
                : `그룹 (${groups.find((g) => g.id === selectedGroup)?.name})`}
            </div>

            <div className="mb-20">
              <strong>최종 메시지:</strong>
              <div
                style={{
                  background: '#f5f5f5',
                  padding: '15px',
                  borderRadius: '5px',
                  whiteSpace: 'pre-wrap',
                  marginTop: '10px',
                }}
              >
                {finalMessage}
              </div>
            </div>

            <div className="flex gap-10">
              <button className="btn btn-outline" onClick={() => setStep(3)}>
                이전
              </button>
              <button
                className="btn btn-primary"
                onClick={handleSend}
                disabled={sending}
              >
                {sending ? '전송 중...' : '메시지 전송'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default ComposeMessage;
