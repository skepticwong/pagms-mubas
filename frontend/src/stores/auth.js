// E:\...\frontend\src\stores\auth.js
import { writable } from 'svelte/store';
import axios from 'axios';

// Enable credentials (for Flask sessions)
axios.defaults.withCredentials = true;

export const user = writable(null);
export const isAuthenticated = writable(false);

export const login = async (email, password) => {
  try {
    const response = await axios.post('http://localhost:5000/api/login', { email, password });
    user.set(response.data);
    isAuthenticated.set(true);
    return { success: true };
  } catch (error) {
    const message = error.response?.data?.error || 'Login failed';
    return { success: false, error: message };
  }
};

export const logout = async () => {
  await axios.post('http://localhost:5000/api/logout');
  user.set(null);
  isAuthenticated.set(false);
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
    const response = await axios.get('http://localhost:5000/api/me');
    user.set(response.data);
    isAuthenticated.set(true);
  } catch {
    user.set(null);
    isAuthenticated.set(false);
  }
};