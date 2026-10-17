import { api } from './api';
import { User, UserRole } from '../types/auth';
import { UserCreateInput, UserUpdateInput, ProfileUpdateInput, PasswordChangeInput } from '../types/user';

export const userService = {
  // Profile Endpoints
  async getProfile(): Promise<User> {
    const response = await api.get<User>('/profile');
    return response.data;
  },

  async updateProfile(data: ProfileUpdateInput): Promise<User> {
    const response = await api.put<User>('/profile', data);
    return response.data;
  },

  async changePassword(data: PasswordChangeInput): Promise<{ message: string }> {
    const response = await api.post<{ message: string }>('/profile/change-password', data);
    return response.data;
  },

  // Admin User Management Endpoints
  async listUsers(): Promise<User[]> {
    const response = await api.get<User[]>('/users');
    return response.data;
  },

  async createUser(data: UserCreateInput): Promise<User> {
    const response = await api.post<User>('/users', data);
    return response.data;
  },

  async updateUserRole(userId: number, role: UserRole): Promise<User> {
    const response = await api.patch<User>(`/users/${userId}/role`, { role });
    return response.data;
  },

  async updateUserStatus(userId: number, isActive: boolean): Promise<User> {
    const response = await api.patch<User>(`/users/${userId}/status`, { is_active: isActive });
    return response.data;
  },
};
