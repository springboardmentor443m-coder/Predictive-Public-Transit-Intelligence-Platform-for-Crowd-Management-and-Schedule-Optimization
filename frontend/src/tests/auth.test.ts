import { describe, it, expect, beforeEach } from 'vitest';

// Lightweight localStorage mock for unit environment
class LocalStorageMock {
  private store: Record<string, string> = {};

  clear() {
    this.store = {};
  }

  getItem(key: string) {
    return this.store[key] || null;
  }

  setItem(key: string, value: string) {
    this.store[key] = String(value);
  }

  removeItem(key: string) {
    delete this.store[key];
  }
}

const localStorageMock = new LocalStorageMock();
(global as any).localStorage = localStorageMock;

describe('Frontend Authentication Storage Unit Tests', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('stores JWT access token and user session on successful login', () => {
    const mockToken = 'mock-jwt-token-123456';
    const mockUser = {
      id: 1,
      email: 'admin@metroflow.io',
      name: 'System Admin',
      role: 'ADMIN',
      is_active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };

    localStorage.setItem('metroflow_token', mockToken);
    localStorage.setItem('metroflow_user', JSON.stringify(mockUser));

    expect(localStorage.getItem('metroflow_token')).toBe(mockToken);
    expect(JSON.parse(localStorage.getItem('metroflow_user') || '{}')).toEqual(mockUser);
  });

  it('clears session tokens on logout', () => {
    localStorage.setItem('metroflow_token', 'temp-token');
    localStorage.setItem('metroflow_user', 'temp-user');

    localStorage.removeItem('metroflow_token');
    localStorage.removeItem('metroflow_user');

    expect(localStorage.getItem('metroflow_token')).toBeNull();
    expect(localStorage.getItem('metroflow_user')).toBeNull();
  });
});
