import React, { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../api/client';
import { User } from '../types';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('metroflow_token'));
  const [user, setUser] = useState<User | null>(() => {
    const savedUser = localStorage.getItem('metroflow_user');
    return savedUser ? JSON.parse(savedUser) : null;
  });

  const login = async (username: string, password: string) => {
    const data = await api.login(username, password);
    const authUser: User = {
      username: data.username,
      role: data.role as 'admin' | 'operator' | 'viewer',
    };
    setToken(data.access_token);
    setUser(authUser);
    localStorage.setItem('metroflow_user', JSON.stringify(authUser));
  };

  const logout = () => {
    api.logout();
    setToken(null);
    setUser(null);
    localStorage.removeItem('metroflow_user');
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!token,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
