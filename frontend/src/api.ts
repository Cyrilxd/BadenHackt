import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "",
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      window.location.reload();
    }
    return Promise.reject(error);
  },
);

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
  is_active: boolean;
}

export const authApi = {
  login: async (username: string, password: string): Promise<LoginResponse> => {
    const formData = new FormData();
    formData.append("username", username);
    formData.append("password", password);

    const response = await api.post<LoginResponse>("/api/login", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return response.data;
  },
};

export const roomsApi = {
  getRooms: async (): Promise<Room[]> => {
    const response = await api.get<Room[]>("/api/rooms");
    return response.data;
  },

  toggleInternet: async (roomId: number, enable: boolean) => {
    const response = await api.post(`/api/rooms/${roomId}/toggle`, null, {
      params: { enable },
    });
    return response.data;
  },
};

export interface AuditEntry {
  id: number;
  timestamp: string;
  username: string;
  action: string;
  target: string | null;
  detail: string | null;
  success: boolean;
}

export const auditApi = {
  getAuditLogs: async (params?: {
    username?: string;
    action?: string;
    success?: boolean;
    limit?: number;
  }): Promise<AuditEntry[]> => {
    const response = await api.get<AuditEntry[]>("/api/audit", { params });
    return response.data;
  },
};

export const whitelistsApi = {
  getWhitelists: async (roomId?: number): Promise<Whitelist[]> => {
    const params = roomId ? { room_id: roomId } : {};
    const response = await api.get<Whitelist[]>("/api/whitelists", { params });
    return response.data;
  },

  createWhitelist: async (
    name: string,
    urls: string[],
    roomId: number,
    isActive: boolean = true,
  ): Promise<Whitelist> => {
    const response = await api.post<Whitelist>("/api/whitelists", {
      name,
      urls,
      room_id: roomId,
      is_active: isActive,
    });
    return response.data;
  },

  updateWhitelist: async (
    id: number,
    name: string,
    urls: string[],
    roomId: number,
    isActive: boolean,
  ): Promise<Whitelist> => {
    const response = await api.put<Whitelist>(`/api/whitelists/${id}`, {
      name,
      urls,
      room_id: roomId,
      is_active: isActive,
    });
    return response.data;
  },

  toggleWhitelist: async (
    id: number,
    roomId: number,
    isActive: boolean,
  ): Promise<Whitelist> => {
    const response = await api.patch<Whitelist>(
      `/api/whitelists/${id}/toggle`,
      {
        room_id: roomId,
        is_active: isActive,
      },
    );
    return response.data;
  },

  deleteWhitelist: async (id: number): Promise<void> => {
    await api.delete(`/api/whitelists/${id}`);
  },
};

export default api;
