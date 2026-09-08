import axios from 'axios';

export const api = axios.create({ baseURL: '/api', timeout: 120000 });

let refreshPromise: Promise<string> | null = null;

async function refreshAccessToken(): Promise<string> {
  const refreshToken = localStorage.getItem('chem_refresh');
  if (!refreshToken) {
    throw new Error('无刷新令牌');
  }
  const res = await axios.post('/api/auth/refresh', { refresh_token: refreshToken });
  const accessToken = res.data.access_token;
  localStorage.setItem('chem_token', accessToken);
  if (res.data.refresh_token) {
    localStorage.setItem('chem_refresh', res.data.refresh_token);
  }
  return accessToken;
}

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('chem_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && original && !original._retry && localStorage.getItem('chem_refresh')) {
      original._retry = true;
      try {
        refreshPromise = refreshPromise || refreshAccessToken();
        const token = await refreshPromise;
        refreshPromise = null;
        original.headers.Authorization = `Bearer ${token}`;
        return api(original);
      } catch (refreshError) {
        refreshPromise = null;
        localStorage.removeItem('chem_token');
        localStorage.removeItem('chem_refresh');
        window.location.hash = '#/login';
        return Promise.reject(refreshError);
      }
    }
    return Promise.reject(error);
  },
);

export async function login(username: string, password: string) {
  const res = await api.post('/auth/login', { username, password });
  localStorage.setItem('chem_token', res.data.access_token);
  localStorage.setItem('chem_refresh', res.data.refresh_token || '');
  localStorage.setItem('chem_user', JSON.stringify(res.data.user ?? {}));
  return res.data;
}

export async function logout() {
  localStorage.removeItem('chem_token');
  localStorage.removeItem('chem_refresh');
  localStorage.removeItem('chem_user');
}
