import React, { createContext, useState, useContext, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { authAPI, userAPI } from '../services/api';

const AuthContext = createContext({});

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Load user from storage on mount
  useEffect(() => {
    loadUser();
  }, []);

  const loadUser = async () => {
    try {
      const token = await AsyncStorage.getItem('accessToken');
      const userData = await AsyncStorage.getItem('user');

      if (token && userData) {
        setUser(JSON.parse(userData));
        setIsAuthenticated(true);

        // Fetch latest user data
        try {
          const response = await userAPI.getMe();
          setUser(response.data);
          await AsyncStorage.setItem('user', JSON.stringify(response.data));
        } catch (error) {
          console.error('Failed to fetch user data:', error);
        }
      }
    } catch (error) {
      console.error('Failed to load user:', error);
    } finally {
      setLoading(false);
    }
  };

  const login = async (username, password) => {
    try {
      const response = await authAPI.login(username, password);
      const { access_token, refresh_token } = response.data;

      await AsyncStorage.setItem('accessToken', access_token);
      await AsyncStorage.setItem('refreshToken', refresh_token);

      // Fetch user data
      const userResponse = await userAPI.getMe();
      setUser(userResponse.data);
      await AsyncStorage.setItem('user', JSON.stringify(userResponse.data));

      setIsAuthenticated(true);
      return { success: true };
    } catch (error) {
      console.error('Login failed:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Login failed',
      };
    }
  };

  const register = async (username, email, password) => {
    try {
      await authAPI.register(username, email, password);
      // Auto-login after registration
      return await login(username, password);
    } catch (error) {
      console.error('Registration failed:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Registration failed',
      };
    }
  };

  const logout = async () => {
    try {
      await authAPI.logout();
      setUser(null);
      setIsAuthenticated(false);
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const updateUser = async (data) => {
    try {
      const response = await userAPI.updateMe(data);
      setUser(response.data);
      await AsyncStorage.setItem('user', JSON.stringify(response.data));
      return { success: true };
    } catch (error) {
      console.error('Update user failed:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Update failed',
      };
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        isAuthenticated,
        login,
        register,
        logout,
        updateUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
