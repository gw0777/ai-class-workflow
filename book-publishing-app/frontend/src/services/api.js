import axios from 'axios';
import { toast } from 'react-toastify';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
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

// Response interceptor
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const message = error.response?.data?.error || error.message || '오류가 발생했습니다.';

    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
      toast.error('인증이 만료되었습니다. 다시 로그인해주세요.');
    } else if (error.response?.status === 403) {
      toast.error('권한이 없습니다.');
    } else if (error.response?.status >= 500) {
      toast.error('서버 오류가 발생했습니다.');
    } else {
      toast.error(message);
    }

    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: (credentials) => api.post('/users/login', credentials),
  register: (userData) => api.post('/users/register', userData),
  getProfile: () => api.get('/users/profile'),
  updateProfile: (userData) => api.put('/users/profile', userData),
};

// Textbook API
export const textbookAPI = {
  getAll: (params) => api.get('/textbooks', { params }),
  getById: (id) => api.get(`/textbooks/${id}`),
  create: (data) => api.post('/textbooks', data),
  update: (id, data) => api.put(`/textbooks/${id}`, data),
  delete: (id) => api.delete(`/textbooks/${id}`),
  publish: (id) => api.post(`/textbooks/${id}/publish`),

  // Chapter operations
  addChapter: (id, data) => api.post(`/textbooks/${id}/chapters`, data),
  updateChapter: (textbookId, chapterId, data) =>
    api.put(`/textbooks/${textbookId}/chapters/${chapterId}`, data),
  deleteChapter: (textbookId, chapterId) =>
    api.delete(`/textbooks/${textbookId}/chapters/${chapterId}`),

  // Assessment operations
  addAssessment: (textbookId, chapterId, data) =>
    api.post(`/textbooks/${textbookId}/chapters/${chapterId}/assessments`, data),
};

// Regulation API
export const regulationAPI = {
  getAll: (params) => api.get('/regulations', { params }),
  getById: (id) => api.get(`/regulations/${id}`),
  create: (data) => api.post('/regulations', data),
  update: (id, data) => api.put(`/regulations/${id}`, data),
  delete: (id) => api.delete(`/regulations/${id}`),
  search: (query, params) => api.get(`/regulations/search?q=${query}`, { params }),
  getByCategory: (category, params) =>
    api.get(`/regulations/category/${category}`, { params }),
  getByCountry: (country, params) =>
    api.get(`/regulations/country/${country}`, { params }),
};

// Upload API
export const uploadAPI = {
  uploadFile: (file, onProgress) => {
    const formData = new FormData();
    formData.append('file', file);

    return api.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress) {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          onProgress(percentCompleted);
        }
      },
    });
  },
};

export default api;
