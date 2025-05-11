import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Chat from './pages/Chat';

// 인증 상태 확인 함수
const isAuthenticated = () => {
  return localStorage.getItem('token') ? true : false;
};

// 보호된 라우트 컴포넌트
const ProtectedRoute = ({ children }) => {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  
  return children;
};

const App = () => {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route 
          path="/chat" 
          element={
            <ProtectedRoute>
              <Chat />
            </ProtectedRoute>
          } 
        />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </Router>
  );
};

export default App; 