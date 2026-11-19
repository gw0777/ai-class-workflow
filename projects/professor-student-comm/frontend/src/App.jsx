import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';

// Pages
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import ProfessorDashboard from './pages/ProfessorDashboard';
import StudentDashboard from './pages/StudentDashboard';
import ComposeMessage from './pages/ComposeMessage';
import GroupManagement from './pages/GroupManagement';

// Protected Route Component
const ProtectedRoute = ({ children, requiredRole }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return <div className="loading"><div className="spinner"></div></div>;
  }

  if (!user) {
    return <Navigate to="/login" />;
  }

  if (requiredRole && user.role !== requiredRole) {
    return <Navigate to="/" />;
  }

  return children;
};

// Route Handler
const AppRoutes = () => {
  const { user } = useAuth();

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      {/* Professor Routes */}
      <Route
        path="/professor/dashboard"
        element={
          <ProtectedRoute requiredRole="professor">
            <ProfessorDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/professor/compose"
        element={
          <ProtectedRoute requiredRole="professor">
            <ComposeMessage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/professor/groups"
        element={
          <ProtectedRoute requiredRole="professor">
            <GroupManagement />
          </ProtectedRoute>
        }
      />

      {/* Student Routes */}
      <Route
        path="/student/dashboard"
        element={
          <ProtectedRoute requiredRole="student">
            <StudentDashboard />
          </ProtectedRoute>
        }
      />

      {/* Default Route */}
      <Route
        path="/"
        element={
          user ? (
            user.role === 'professor' ? (
              <Navigate to="/professor/dashboard" />
            ) : (
              <Navigate to="/student/dashboard" />
            )
          ) : (
            <Navigate to="/login" />
          )
        }
      />
    </Routes>
  );
};

function App() {
  return (
    <Router>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </Router>
  );
}

export default App;
