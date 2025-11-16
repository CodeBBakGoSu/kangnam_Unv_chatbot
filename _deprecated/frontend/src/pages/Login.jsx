import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { authService } from '../utils/api';

const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    
    if (!username || !password) {
      setError('아이디와 비밀번호를 입력해주세요.');
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      const response = await authService.login(username, password);
      
      if (response.token) {
        localStorage.setItem('token', response.token);
        navigate('/chat');
      } else {
        setError('로그인에 실패했습니다.');
      }
    } catch (err) {
      setError('로그인 처리 중 오류가 발생했습니다. 다시 시도해주세요.');
      console.error('Login error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-[#f7f9fc]">
      <div className="w-full max-w-md p-8 bg-white rounded-2xl shadow-lg">
        {/* 로고 영역 */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-20 h-20 flex items-center justify-center rounded-full bg-[#4A69BD] text-white mb-2">
            <div className="text-center">
              <div>강남대학교</div>
              <div>챗봇</div>
            </div>
          </div>
        </div>
        
        <h2 className="text-center text-2xl font-bold text-gray-800 mb-6">
          학생 포털 로그인
        </h2>
        
        {error && (
          <div className="mb-4 p-3 bg-red-100 text-red-700 rounded-md text-sm">
            {error}
          </div>
        )}
        
        <form onSubmit={handleLogin}>
          <div className="mb-4">
            <input
              type="text"
              className="w-full px-4 py-3 rounded-md border border-gray-300 bg-[#f5f8fc] focus:outline-none focus:ring-2 focus:ring-[#4A69BD]"
              placeholder="아이디"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              disabled={loading}
            />
          </div>
          
          <div className="mb-6">
            <input
              type="password"
              className="w-full px-4 py-3 rounded-md border border-gray-300 bg-[#f5f8fc] focus:outline-none focus:ring-2 focus:ring-[#4A69BD]"
              placeholder="비밀번호"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
            />
          </div>
          
          <button
            type="submit"
            className="w-full py-3 rounded-full bg-[#4A69BD] text-white font-medium hover:bg-[#3A59AD] transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#4A69BD] disabled:opacity-70"
            disabled={loading}
          >
            {loading ? '로그인 중...' : '로그인'}
          </button>
        </form>
        
        <p className="mt-6 text-center text-sm text-gray-600">
          학교 계정으로 로그인하여 챗봇 서비스를 이용하세요
        </p>
        
        <div className="mt-12 text-center text-xs text-gray-500">
          © 2025 강남대학교 AI 챗봇 서비스
        </div>
      </div>
    </div>
  );
};

export default Login; 