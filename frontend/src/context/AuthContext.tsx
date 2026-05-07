import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User } from '../types';
import { authApi } from '../services/api';

interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => Promise<boolean>;
  signup: (name: string, email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  logout: () => void;
  updateUser: (patch: Partial<User>) => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('voyonata_token');
    if (token) {
      authApi.me(token)
        .then(data => {
          const u: User = { name: data.full_name, email: data.email };
          setUser(u);
          localStorage.setItem('voyonata_user', JSON.stringify(u));
        })
        .catch(() => {
          localStorage.removeItem('voyonata_token');
          localStorage.removeItem('voyonata_user');
        })
        .finally(() => setIsLoading(false));
    } else {
      const stored = localStorage.getItem('voyonata_user');
      if (stored) {
        try { setUser(JSON.parse(stored)); } catch { localStorage.removeItem('voyonata_user'); }
      }
      setIsLoading(false);
    }
  }, []);

  const login = async (email: string, password: string): Promise<boolean> => {
    try {
      const { access_token } = await authApi.login(email, password);
      localStorage.setItem('voyonata_token', access_token);
      const data = await authApi.me(access_token);
      const u: User = { name: data.full_name, email: data.email };
      setUser(u);
      localStorage.setItem('voyonata_user', JSON.stringify(u));
      return true;
    } catch {
      return false;
    }
  };

  const signup = async (
    name: string,
    email: string,
    password: string,
  ): Promise<{ success: boolean; error?: string }> => {
    try {
      const { access_token } = await authApi.signup(email, password, name);
      localStorage.setItem('voyonata_token', access_token);
      const data = await authApi.me(access_token);
      const u: User = { name: data.full_name, email: data.email };
      setUser(u);
      localStorage.setItem('voyonata_user', JSON.stringify(u));
      return { success: true };
    } catch (err) {
      return { success: false, error: (err as Error).message };
    }
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('voyonata_token');
    localStorage.removeItem('voyonata_user');
  };

  const updateUser = (patch: Partial<User>) => {
    setUser(prev => prev ? { ...prev, ...patch } : prev);
  };

  return (
    <AuthContext.Provider value={{ user, login, signup, logout, updateUser, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
