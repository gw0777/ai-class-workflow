import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export const useAuthStore = create(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,

      setAuth: (user, token) => {
        set({ user, token, isAuthenticated: true });
        // 토큰을 localStorage에 저장하여 axios 인터셉터에서 사용
        localStorage.setItem('token', token);
      },

      clearAuth: () => {
        set({ user: null, token: null, isAuthenticated: false });
        localStorage.removeItem('token');
      },

      updateUser: (userData) => {
        set((state) => ({
          user: { ...state.user, ...userData }
        }));
      },

      isAdmin: () => {
        const { user } = get();
        return user?.role === 'ADMIN';
      },

      isEditor: () => {
        const { user } = get();
        return user?.role === 'ADMIN' || user?.role === 'EDITOR';
      },

      isReviewer: () => {
        const { user } = get();
        return user?.role === 'ADMIN' || user?.role === 'EDITOR' || user?.role === 'REVIEWER';
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
