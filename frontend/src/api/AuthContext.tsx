import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { api, clearToken, getToken, setToken } from "../api/client";
import type { User } from "../types/api";

interface AuthState {
  user: User | null;
  loading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthState | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function bootstrap() {
      if (!getToken()) {
        setLoading(false);
        return;
      }
      try {
        const me = await api.me();
        setUser(me);
      } catch {
        clearToken();
      } finally {
        setLoading(false);
      }
    }
    bootstrap();
  }, []);

  async function login(email: string, password: string) {
    setError(null);
    try {
      const { access_token } = await api.login(email, password);
      setToken(access_token);
      const me = await api.me();
      setUser(me);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Login failed");
      throw e;
    }
  }

  async function register(email: string, password: string, fullName: string) {
    setError(null);
    try {
      await api.register(email, password, fullName);
      await login(email, password);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Registration failed");
      throw e;
    }
  }

  function logout() {
    clearToken();
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, loading, error, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
