import axios from 'axios';
import { User, Task, Document } from '../types';

// Use relative URL for production build where frontend and backend are served from same origin
const API_URL = import.meta.env.PROD ? '' : `http://${window.location.hostname}:3001`;

const api = axios.create({
  baseURL: API_URL,
});

export const userService = {
  getAll: () => api.get<User[]>('/users').then(res => res.data),
  getById: (id: string) => api.get<User>(`/users/${id}`).then(res => res.data),
  create: (user: User) => api.post<User>('/users', user).then(res => res.data),
  update: (id: string, user: Partial<User>) => api.patch<User>(`/users/${id}`, user).then(res => res.data),
  delete: (id: string) => api.delete(`/users/${id}`).then(res => res.data),
};

export const taskService = {
  getAll: () => api.get<Task[]>('/tasks').then(res => res.data),
  create: (task: Task) => api.post<Task>('/tasks', task).then(res => res.data),
  update: (id: string, task: Partial<Task>) => api.patch<Task>(`/tasks/${id}`, task).then(res => res.data),
  delete: (id: string) => api.delete(`/tasks/${id}`).then(res => res.data),
};

export const documentService = {
  getAll: () => api.get<Document[]>('/documents').then(res => res.data),
  create: (doc: Document) => api.post<Document>('/documents', doc).then(res => res.data),
  delete: (id: string) => api.delete(`/documents/${id}`).then(res => res.data),
};

export default api;