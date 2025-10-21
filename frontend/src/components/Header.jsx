import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

function Header() {
  const { user, logout, isProfessor } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="header">
      <div className="header-content">
        <div>
          <h2>교수-학생 AI 소통 플랫폼</h2>
          <p style={{ color: '#666', fontSize: '14px' }}>
            {user?.name} ({user?.role === 'professor' ? '교수' : '학생'})
          </p>
        </div>

        <div className="flex gap-10">
          {isProfessor() && (
            <>
              <Link to="/professor/dashboard" className="btn btn-outline">
                대시보드
              </Link>
              <Link to="/professor/compose" className="btn btn-secondary">
                메시지 작성
              </Link>
              <Link to="/professor/groups" className="btn btn-outline">
                그룹 관리
              </Link>
            </>
          )}

          <button onClick={handleLogout} className="btn btn-danger">
            로그아웃
          </button>
        </div>
      </div>
    </div>
  );
}

export default Header;
