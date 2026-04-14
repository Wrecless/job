import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

export type ApiParams = Record<string, string | number | boolean | null | undefined>;
export type ApiPayload = Record<string, unknown>;

const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
});

export const jobsAPI = {
  list: (params?: ApiParams) => api.get('/jobs/', { params }),
};

export const applicationsAPI = {
  list: () => api.get('/applications/'),
  create: (job_id: string) => api.post('/applications/', { job_id }),
  update: (id: string, data: ApiPayload) => api.patch(`/applications/${id}`, data),
  delete: (id: string) => api.delete(`/applications/${id}`),
  tasks: () => api.get('/applications/tasks/pending'),
};

export const alertsAPI = {
  list: () => api.get('/alerts/'),
  markRead: (id: string) => api.patch(`/alerts/${id}/read`),
  updateStatus: (id: string, status: string) => api.patch(`/alerts/${id}/status`, { status }),
};

export const botAPI = {
  run: () => api.post('/bot/run'),
};

export const sourcesAPI = {
  list: () => api.get('/sources/'),
  create: (data: { name: string; source_type: string; base_url: string; is_active: boolean }) => api.post('/sources/', data),
  update: (id: string, data: Partial<{ name: string; source_type: string; base_url: string; is_active: boolean }>) =>
    api.patch(`/sources/${id}`, data),
  delete: (id: string) => api.delete(`/sources/${id}`),
};

export default api;
