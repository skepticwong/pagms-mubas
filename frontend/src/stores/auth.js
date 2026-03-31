// E:\...\frontend\src\stores\auth.js
import { writable } from 'svelte/store';
import axios from 'axios';

// Enable credentials (for Flask sessions)
// Dynamic API base URL to handle localhost vs 127.0.0.1 consistently
const API_BASE_URL = '/api';

// Enable credentials (for Flask sessions) - ensures global defaults
axios.defaults.withCredentials = true;

export const user = writable(null);
export const isAuthenticated = writable(false);

export const login = async (email, password) => {
  try {
    console.log('Attempting login to:', `${API_BASE_URL}/login`);
    const response = await axios.post(`${API_BASE_URL}/login`, { email, password });
    console.log('Login response:', response);
    
    // Save JWT token to localStorage for API requests
    if (response.data.token) {
      localStorage.setItem('token', response.data.token);
    }
    
    user.set(response.data);
    isAuthenticated.set(true);
    return { success: true, user: response.data };
  } catch (error) {
    console.error('Login error:', error);
    console.error('Error details:', {
      message: error.message,
      code: error.code,
      response: error.response?.status,
      data: error.response?.data
    });
    const message = error.response?.data?.error || error.message || 'Login failed';
    return { success: false, error: message };
  }
};

export const logout = async () => {
  try {
    console.log('Attempting logout to:', `${API_BASE_URL}/logout`);
    const response = await axios.post(`${API_BASE_URL}/logout`);
    console.log('Logout response:', response);
    
    // Clear JWT token from localStorage
    localStorage.removeItem('token');
    
    user.set(null);
    isAuthenticated.set(false);
  } catch (error) {
    console.error('Logout error:', error);
    console.error('Error details:', {
      message: error.message,
      code: error.code,
      response: error.response?.status,
      data: error.response?.data
    });
    // Still clear local data even if logout request fails
    localStorage.removeItem('token');
    user.set(null);
    isAuthenticated.set(false);
  }
};

export const register = async (name, email, password, role, pay_rate = null) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/register`, {
      name,
      email,
      password,
      role,
      pay_rate
    });
    user.set(response.data);
    isAuthenticated.set(true);
    return { success: true };
  } catch (error) {
    const message = error.response?.data?.error || 'Registration failed';
    return { success: false, error: message };
  }
};

export const checkAuth = async () => {
  try {
    console.log('Checking auth at:', `${API_BASE_URL}/me`);
    const response = await axios.get(`${API_BASE_URL}/me`);
    console.log('Auth check response:', response);
    user.set(response.data);
    isAuthenticated.set(true);
  } catch (error) {
    console.error('Auth check error:', error);
    console.error('Error details:', {
      message: error.message,
      code: error.code,
      response: error.response?.status,
      data: error.response?.data
    });
    user.set(null);
    isAuthenticated.set(false);
  }
};