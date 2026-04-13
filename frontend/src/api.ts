import axios from 'axios';

const API_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authAPI = {
  register: (email: string, password: string) =>
    api.post('/auth/register', { email, password }),
  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }),
  refresh: (refresh_token: string) =>
    api.post('/auth/refresh', { refresh_token }),
};

export const profileAPI = {
  get: () => api.get('/profile/'),
  create: (data: any) => api.post('/profile/', data),
  update: (data: any) => api.put('/profile/', data),
  patch: (data: any) => api.patch('/profile/', data),
};

export const resumeAPI = {
  list: () => api.get('/resumes/'),
  upload: (formData: FormData) =>
    api.post('/resumes/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  delete: (id: string) => api.delete(`/resumes/${id}`),
};

export const sourcesAPI = {
  list: () => api.get('/sources/'),
  create: (data: any) => api.post('/sources/', data),
  delete: (name: string) => api.delete(`/sources/${name}`),
  fetch: () => api.post('/automation/fetch-jobs'),
  status: () => api.get('/automation/scheduler-status'),
};

export const jobsAPI = {
  list: (params?: any) => api.get('/jobs/', { params }),
  get: (id: string) => api.get(`/jobs/${id}`),
  search: (params?: any) => api.get('/jobs/search', { params }),
};

export const applicationsAPI = {
  list: () => api.get('/applications/'),
  create: (job_id: string) => api.post('/applications/', { job_id }),
  update: (id: string, data: any) => api.patch(`/applications/${id}`, data),
  tasks: () => api.get('/applications/tasks/pending'),
};

export const tailoringAPI = {
  tailor: (job_id: string, resume_id?: string, use_ai?: boolean) =>
    api.post('/tailor/', { job_id, resume_id, use_ai }),
  tailorResume: (job_id: string, resume_id?: string, use_ai?: boolean) =>
    api.post('/tailor/resume', { job_id, resume_id, use_ai }),
  coverLetter: (job_id: string, resume_id?: string) =>
    api.post('/tailor/cover-letter', { job_id, resume_id }),
};

export default api;
