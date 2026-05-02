import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' },
});

// HU01: Inyectar token JWT en cada request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('qa_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// HU01: Si el backend devuelve 401, limpiar sesion y redirigir al login
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('qa_token');
      localStorage.removeItem('qa_user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
