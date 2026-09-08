import axios from 'axios';

export const api = axios.create({ baseURL: '/api', timeout: 120000 });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('chem_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export async function login(username: string, password: string) {
  const res = await api.post('/auth/login', { username, password });
  localStorage.setItem('chem_token', res.data.access_token);
  localStorage.setItem('chem_user', JSON.stringify(res.data.user ?? {}));
  return res.data;
}

export async function logout() {
  localStorage.removeItem('chem_token');
  localStorage.removeItem('chem_user');
}
