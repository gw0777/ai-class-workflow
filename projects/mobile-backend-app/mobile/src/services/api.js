import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Base URL - change this to your backend URL
const API_BASE_URL = 'http://localhost:8000/api/v1';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  async (config) => {
    const token = await AsyncStorage.getItem('accessToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If token expired, try to refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = await AsyncStorage.getItem('refreshToken');
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });

          const { access_token } = response.data;
          await AsyncStorage.setItem('accessToken', access_token);

          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        // Refresh failed, logout user
        await AsyncStorage.multiRemove(['accessToken', 'refreshToken', 'user']);
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  register: (username, email, password) =>
    api.post('/auth/register', { username, email, password }),

  login: (username, password) => {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);

    return api.post('/auth/login', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  logout: async () => {
    await AsyncStorage.multiRemove(['accessToken', 'refreshToken', 'user']);
  },
};

// User API
export const userAPI = {
  getMe: () => api.get('/users/me'),

  updateMe: (data) => api.put('/users/me', data),

  deleteMe: () => api.delete('/users/me'),
};

// Activity API
export const activityAPI = {
  create: (activityData) => api.post('/activities', activityData),

  getAll: (params) => api.get('/activities', { params }),

  getById: (id) => api.get(`/activities/${id}`),

  update: (id, data) => api.put(`/activities/${id}`, data),

  delete: (id) => api.delete(`/activities/${id}`),
};

export default api;
