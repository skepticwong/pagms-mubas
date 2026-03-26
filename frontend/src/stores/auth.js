// E:\...\frontend\src\stores\auth.js
import { writable } from 'svelte/store';
import axios from 'axios';

// Enable credentials (for Flask sessions)
axios.defaults.withCredentials = true;

export const user = writable(null);
export const isAuthenticated = writable(false);

export const login = async (email, password) => {
  try {
    console.log('Attempting login to:', 'http://localhost:5000/api/login');
    const response = await axios.post('http://localhost:5000/api/login', { email, password });
    console.log('Login response:', response);
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
    console.log('Attempting logout to:', 'http://localhost:5000/api/logout');
    const response = await axios.post('http://localhost:5000/api/logout');
    console.log('Logout response:', response);
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
  }
};

export const register = async (name, email, password, role, pay_rate = null) => {
  try {
    const response = await axios.post('http://localhost:5000/api/register', {
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
    console.log('Checking auth at:', 'http://localhost:5000/api/me');
    const response = await axios.get('http://localhost:5000/api/me');
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