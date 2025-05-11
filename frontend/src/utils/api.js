import axios from 'axios';

// Axios 인스턴스 생성
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  }
});

// 요청 인터셉터 설정
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    console.error('API 요청 오류:', error);
    return Promise.reject(error);
  }
);

// 응답 인터셉터 설정
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // 401 오류 처리 (인증 만료)
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// API 서비스 함수들
export const authService = {
  login: async (username, password) => {
    const response = await api.post('/api/auth/login', { username, password });
    // 백엔드 응답(access_token)을 프론트엔드 형식(token)으로 변환
    return {
      token: response.data.access_token,
      token_type: response.data.token_type
    };
  },
  logout: () => {
    localStorage.removeItem('token');
    window.location.href = '/login';
  }
};

export const chatService = {
  sendMessage: async (message) => {
    const response = await api.post('/api/chat', { message });
    return response.data;
  }
};

export default api; 