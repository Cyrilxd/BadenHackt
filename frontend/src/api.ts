import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: {
    username: string;
    role: string;
  };
}

export interface Room {
  id: number;
  name: string;
  subnet: string;
  vlan_id: number;
  internet_enabled: boolean;
}

export interface Whitelist {
  id: number;
  name: string;
  urls: string[];
  room_id: number;
}

export const authApi = {
  login: async (username: string, password: string): Promise<LoginResponse> => {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    
    const response = await api.post<LoginResponse>('/api/login', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
};

export const roomsApi = {
  getRooms: async (): Promise<Room[]> => {
    const response = await api.get<Room[]>('/api/rooms');
    return response.data;
  },
  
  toggleInternet: async (roomId: number, enable: boolean): Promise<{ success: boolean; internet_enabled: boolean }> => {
    const response = await api.post(`/api/rooms/${roomId}/toggle`, null, {
      params: { enable },
    });
    return response.data;
  },
};

export const whitelistsApi = {
  getWhitelists: async (roomId?: number): Promise<Whitelist[]> => {
    const params = roomId ? { room_id: roomId } : {};
    const response = await api.get<Whitelist[]>('/api/whitelists', { params });
    return response.data;
  },
  
  createWhitelist: async (name: string, urls: string[], roomId: number): Promise<Whitelist> => {
    const response = await api.post<Whitelist>('/api/whitelists', { name, urls, room_id: roomId });
    return response.data;
  },
  
  deleteWhitelist: async (id: number): Promise<void> => {
    await api.delete(`/api/whitelists/${id}`);
  },
};

export default api;
