import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:3000/api';

// Axios 인스턴스 생성
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 요청 인터셉터: JWT 토큰 자동 추가
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 응답 인터셉터: 에러 처리
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // 인증 오류 시 로그아웃
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
  getCurrentUser: () => api.get('/auth/me'),
};

// Message API
export const messageAPI = {
  analyzeMessage: (data) => api.post('/messages/analyze', data),
  createDraft: (data) => api.post('/messages/draft', data),
  sendMessage: (messageId, data) => api.post(`/messages/${messageId}/send`, data),
  getSentMessages: () => api.get('/messages/sent'),
  getReceivedMessages: () => api.get('/messages/received'),
  markAsRead: (messageId) => api.put(`/messages/${messageId}/read`),
  addReaction: (messageId, reaction) => api.post(`/messages/${messageId}/reaction`, { reaction }),
};

// Group API
export const groupAPI = {
  createGroup: (data) => api.post('/groups', data),
  getGroups: () => api.get('/groups'),
  getGroupDetails: (groupId) => api.get(`/groups/${groupId}`),
  addStudents: (groupId, studentIds) => api.post(`/groups/${groupId}/students`, { studentIds }),
  removeStudent: (groupId, studentId) => api.delete(`/groups/${groupId}/students/${studentId}`),
  deleteGroup: (groupId) => api.delete(`/groups/${groupId}`),
};

// User API
export const userAPI = {
  getStudents: () => api.get('/users/students'),
  searchStudents: (query) => api.get('/users/students/search', { params: { query } }),
  getStudent: (studentId) => api.get(`/users/students/${studentId}`),
};

export default api;
