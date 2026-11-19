import React, { useState, useEffect } from 'react';
import Header from '../components/Header';
import { groupAPI, userAPI } from '../services/api';

function GroupManagement() {
  const [groups, setGroups] = useState([]);
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [groupDetails, setGroupDetails] = useState(null);
  const [students, setStudents] = useState([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showAddStudents, setShowAddStudents] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [newGroup, setNewGroup] = useState({ name: '', description: '' });
  const [selectedStudents, setSelectedStudents] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadGroups();
    loadStudents();
  }, []);

  const loadGroups = async () => {
    try {
      const response = await groupAPI.getGroups();
      setGroups(response.data.groups);
    } catch (err) {
      setError('그룹 목록을 불러오는 중 오류가 발생했습니다.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadStudents = async () => {
    try {
      const response = await userAPI.getStudents();
      setStudents(response.data.students);
    } catch (err) {
      console.error('Failed to load students:', err);
    }
  };

  const loadGroupDetails = async (groupId) => {
    try {
      const response = await groupAPI.getGroupDetails(groupId);
      setGroupDetails(response.data);
      setSelectedGroup(groupId);
    } catch (err) {
      alert('그룹 정보를 불러오는 중 오류가 발생했습니다.');
      console.error(err);
    }
  };

  const handleCreateGroup = async (e) => {
    e.preventDefault();

    if (!newGroup.name.trim()) {
      alert('그룹 이름을 입력해주세요.');
      return;
    }

    try {
      await groupAPI.createGroup({
        name: newGroup.name,
        description: newGroup.description,
        studentIds: selectedStudents,
      });

      alert('그룹이 생성되었습니다.');
      setShowCreateForm(false);
      setNewGroup({ name: '', description: '' });
      setSelectedStudents([]);
      loadGroups();
    } catch (err) {
      alert('그룹 생성 중 오류가 발생했습니다.');
      console.error(err);
    }
  };

  const handleAddStudents = async () => {
    if (selectedStudents.length === 0) {
      alert('추가할 학생을 선택해주세요.');
      return;
    }

    try {
      await groupAPI.addStudents(selectedGroup, selectedStudents);
      alert('학생이 추가되었습니다.');
      setShowAddStudents(false);
      setSelectedStudents([]);
      loadGroupDetails(selectedGroup);
    } catch (err) {
      alert('학생 추가 중 오류가 발생했습니다.');
      console.error(err);
    }
  };

  const handleRemoveStudent = async (studentId) => {
    if (!confirm('정말 이 학생을 그룹에서 제거하시겠습니까?')) {
      return;
    }

    try {
      await groupAPI.removeStudent(selectedGroup, studentId);
      alert('학생이 제거되었습니다.');
      loadGroupDetails(selectedGroup);
    } catch (err) {
      alert('학생 제거 중 오류가 발생했습니다.');
      console.error(err);
    }
  };

  const handleDeleteGroup = async (groupId) => {
    if (!confirm('정말 이 그룹을 삭제하시겠습니까?')) {
      return;
    }

    try {
      await groupAPI.deleteGroup(groupId);
      alert('그룹이 삭제되었습니다.');
      setSelectedGroup(null);
      setGroupDetails(null);
      loadGroups();
    } catch (err) {
      alert('그룹 삭제 중 오류가 발생했습니다.');
      console.error(err);
    }
  };

  const handleStudentToggle = (studentId) => {
    setSelectedStudents((prev) =>
      prev.includes(studentId)
        ? prev.filter((id) => id !== studentId)
        : [...prev, studentId]
    );
  };

  const availableStudents = groupDetails
    ? students.filter(
        (s) => !groupDetails.members.some((m) => m.id === s.id)
      )
    : students;

  const filteredStudents = availableStudents.filter(
    (s) =>
      s.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.email.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div>
      <Header />
      <div className="container">
        <div className="flex-between mb-20">
          <h1>그룹 관리</h1>
          <button
            className="btn btn-primary"
            onClick={() => setShowCreateForm(!showCreateForm)}
          >
            {showCreateForm ? '취소' : '새 그룹 만들기'}
          </button>
        </div>

        {error && <div className="alert alert-danger">{error}</div>}

        {/* 그룹 생성 폼 */}
        {showCreateForm && (
          <div className="card mb-20">
            <h2 className="mb-20">새 그룹 만들기</h2>
            <form onSubmit={handleCreateGroup}>
              <div className="form-group">
                <label>그룹 이름 *</label>
                <input
                  type="text"
                  value={newGroup.name}
                  onChange={(e) =>
                    setNewGroup({ ...newGroup, name: e.target.value })
                  }
                  placeholder="예: 2024 체육교육론 A반"
                  required
                />
              </div>

              <div className="form-group">
                <label>설명</label>
                <textarea
                  value={newGroup.description}
                  onChange={(e) =>
                    setNewGroup({ ...newGroup, description: e.target.value })
                  }
                  placeholder="그룹에 대한 설명을 입력하세요"
                  rows={3}
                />
              </div>

              <div className="form-group">
                <label>학생 선택 (선택사항)</label>
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="학생 검색"
                />
              </div>

              <div style={{ maxHeight: '200px', overflowY: 'auto', marginBottom: '20px' }}>
                {filteredStudents.map((student) => (
                  <div
                    key={student.id}
                    style={{
                      padding: '10px',
                      borderBottom: '1px solid #eee',
                      display: 'flex',
                      gap: '10px',
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={selectedStudents.includes(student.id)}
                      onChange={() => handleStudentToggle(student.id)}
                    />
                    <div>
                      <div>{student.name}</div>
                      <div style={{ fontSize: '12px', color: '#666' }}>
                        {student.email}
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <button type="submit" className="btn btn-primary">
                그룹 생성
              </button>
            </form>
          </div>
        )}

        <div className="grid" style={{ gridTemplateColumns: '1fr 2fr', gap: '20px' }}>
          {/* 그룹 목록 */}
          <div className="card">
            <h2 className="mb-20">그룹 목록</h2>

            {loading && (
              <div className="loading">
                <div className="spinner"></div>
              </div>
            )}

            {!loading && groups.length === 0 && (
              <p className="text-center" style={{ padding: '20px', color: '#666' }}>
                생성된 그룹이 없습니다.
              </p>
            )}

            {!loading && groups.length > 0 && (
              <ul className="message-list">
                {groups.map((group) => (
                  <li
                    key={group.id}
                    className="message-item"
                    onClick={() => loadGroupDetails(group.id)}
                    style={{
                      cursor: 'pointer',
                      borderLeft:
                        selectedGroup === group.id
                          ? '4px solid #2196F3'
                          : '4px solid #4CAF50',
                    }}
                  >
                    <div style={{ fontWeight: '500' }}>{group.name}</div>
                    <div style={{ fontSize: '12px', color: '#666', marginTop: '5px' }}>
                      {group.member_count}명
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* 그룹 상세 정보 */}
          <div className="card">
            {groupDetails ? (
              <>
                <div className="flex-between mb-20">
                  <div>
                    <h2>{groupDetails.group.name}</h2>
                    <p style={{ color: '#666' }}>
                      {groupDetails.group.description || '설명 없음'}
                    </p>
                  </div>
                  <button
                    className="btn btn-danger"
                    onClick={() => handleDeleteGroup(selectedGroup)}
                  >
                    그룹 삭제
                  </button>
                </div>

                <div className="flex-between mb-20">
                  <h3>그룹 멤버 ({groupDetails.members.length}명)</h3>
                  <button
                    className="btn btn-secondary"
                    onClick={() => {
                      setShowAddStudents(!showAddStudents);
                      setSelectedStudents([]);
                      setSearchQuery('');
                    }}
                  >
                    {showAddStudents ? '취소' : '학생 추가'}
                  </button>
                </div>

                {/* 학생 추가 폼 */}
                {showAddStudents && (
                  <div style={{ marginBottom: '20px', background: '#f5f5f5', padding: '15px', borderRadius: '5px' }}>
                    <div className="form-group">
                      <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder="학생 검색"
                      />
                    </div>

                    <div style={{ maxHeight: '200px', overflowY: 'auto', marginBottom: '10px' }}>
                      {filteredStudents.map((student) => (
                        <div
                          key={student.id}
                          style={{
                            padding: '10px',
                            background: 'white',
                            marginBottom: '5px',
                            borderRadius: '3px',
                            display: 'flex',
                            gap: '10px',
                          }}
                        >
                          <input
                            type="checkbox"
                            checked={selectedStudents.includes(student.id)}
                            onChange={() => handleStudentToggle(student.id)}
                          />
                          <div>
                            <div>{student.name}</div>
                            <div style={{ fontSize: '12px', color: '#666' }}>
                              {student.email}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>

                    <button
                      className="btn btn-primary"
                      onClick={handleAddStudents}
                      disabled={selectedStudents.length === 0}
                    >
                      선택한 학생 추가 ({selectedStudents.length})
                    </button>
                  </div>
                )}

                {/* 멤버 목록 */}
                {groupDetails.members.length === 0 ? (
                  <p className="text-center" style={{ padding: '20px', color: '#666' }}>
                    그룹에 학생이 없습니다.
                  </p>
                ) : (
                  <ul className="message-list">
                    {groupDetails.members.map((member) => (
                      <li key={member.id} className="message-item">
                        <div className="flex-between">
                          <div>
                            <div style={{ fontWeight: '500' }}>{member.name}</div>
                            <div style={{ fontSize: '12px', color: '#666' }}>
                              {member.email}
                              {member.studentId && ` (${member.studentId})`}
                            </div>
                          </div>
                          <button
                            className="btn btn-outline"
                            style={{ borderColor: '#f44336', color: '#f44336' }}
                            onClick={() => handleRemoveStudent(member.id)}
                          >
                            제거
                          </button>
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </>
            ) : (
              <div className="flex-center" style={{ height: '100%', color: '#999' }}>
                그룹을 선택하세요
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default GroupManagement;
