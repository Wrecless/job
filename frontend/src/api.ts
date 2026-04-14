import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
});

export const jobsAPI = {
  list: (params?: any) => api.get('/jobs/', { params }),
};

export const applicationsAPI = {
  list: () => api.get('/applications/'),
  create: (job_id: string) => api.post('/applications/', { job_id }),
  update: (id: string, data: any) => api.patch(`/applications/${id}`, data),
  delete: (id: string) => api.delete(`/applications/${id}`),
  tasks: () => api.get('/applications/tasks/pending'),
};

export const alertsAPI = {
  list: () => api.get('/alerts/'),
  markRead: (id: string) => api.patch(`/alerts/${id}/read`),
  updateStatus: (id: string, status: string) => api.patch(`/alerts/${id}/status`, { status }),
};

export default api;
