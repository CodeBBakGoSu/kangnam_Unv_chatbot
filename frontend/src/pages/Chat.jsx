import React, { useEffect } from 'react';
import { authService } from '../utils/api';

const Chat = () => {
  useEffect(() => {
    // 토큰 유효성 확인
    const token = localStorage.getItem('token');
    if (!token) {
      authService.logout();
      return;
    }
    
    // Streamlit URL로 리다이렉션 (토큰 포함)
    const streamlitUrl = 'http://192.168.0.160:8501';
    const redirectUrl = `${streamlitUrl}?token=${encodeURIComponent(token)}`;
    
    // 자동 리다이렉트 타이머 설정 (3초 후)
    const redirectTimer = setTimeout(() => {
      window.location.href = redirectUrl;
    }, 3000);
    
    return () => {
      clearTimeout(redirectTimer);
    };
  }, []);
  
  const handleLogout = () => {
    authService.logout();
  };
  
  // Streamlit URL 직접 이동
  const handleDirectRedirect = () => {
    const token = localStorage.getItem('token');
    const streamlitUrl = 'http://192.168.0.160:8501';
    const redirectUrl = `${streamlitUrl}?token=${encodeURIComponent(token)}`;
    window.location.href = redirectUrl;
  };
  
  return (
    <div className="min-h-screen bg-background flex items-center justify-center flex-col p-4">
      <div className="bg-white rounded-xl shadow-lg p-8 max-w-md w-full text-center">
        <div className="mb-8">
          <div className="w-20 h-20 mx-auto flex items-center justify-center rounded-full bg-primary text-white mb-6">
            <div className="text-center">
              <div>강남대</div>
              <div>챗봇</div>
            </div>
          </div>
          
          <h1 className="text-2xl font-bold text-gray-800 mb-4">챗봇 서비스로 이동합니다</h1>
          <p className="text-gray-600 mb-6">잠시 후 자동으로 챗봇 인터페이스로 이동합니다.</p>
          
          <div className="flex items-center justify-center space-x-3 mb-4">
            <span className="w-3 h-3 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0s' }}></span>
            <span className="w-3 h-3 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></span>
            <span className="w-3 h-3 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></span>
          </div>
        </div>
        
        <div className="flex justify-between">
          <button 
            onClick={handleDirectRedirect}
            className="px-6 py-2 bg-primary text-white rounded-full hover:bg-secondary transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary"
          >
            지금 이동
          </button>
          
          <button 
            onClick={handleLogout}
            className="px-6 py-2 bg-gray-200 text-gray-700 rounded-full hover:bg-gray-300 transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-400"
          >
            로그아웃
          </button>
        </div>
      </div>
    </div>
  );
};

export default Chat; 