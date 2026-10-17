import { UserRole } from './auth';

export interface UserCreateInput {
  email: string;
  name: string;
  password: string;
  role: UserRole;
  is_active: boolean;
}

export interface UserUpdateInput {
  name?: string;
  email?: string;
  role?: UserRole;
  is_active?: boolean;
}

export interface ProfileUpdateInput {
  name?: string;
  email?: string;
}

export interface PasswordChangeInput {
  current_password: string;
  new_password: string;
}
