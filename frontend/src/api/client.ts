import type { Application, ScanResult, Skill, User } from "../types/api";

// In dev, Vite proxies /api -> http://localhost:8000 (see vite.config.ts).
// In production, point this at your deployed API origin.
const BASE = "/api";

const TOKEN_KEY = "signalwork_token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    ...(options.body ? { "Content-Type": "application/json" } : {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers as Record<string, string> | undefined),
  };

  const res = await fetch(`${BASE}${path}`, { ...options, headers });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      // ignore non-JSON error bodies
    }
    throw new Error(detail);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

export interface Page<T> {
  items: T[];
  meta: {
    total: number;
    page: number;
    page_size: number;
    has_next: boolean;
  };
}

export const api = {
  async register(email: string, password: string, full_name: string): Promise<User> {
    return request<User>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, full_name }),
    });
  },

  async login(email: string, password: string): Promise<{ access_token: string }> {
    const form = new URLSearchParams();
    form.set("username", email);
    form.set("password", password);
    const res = await fetch(`${BASE}/auth/login`, { method: "POST", body: form });
    if (!res.ok) throw new Error("Incorrect email or password");
    return res.json();
  },

  async me(): Promise<User> {
    return request<User>("/profile/me");
  },

  async listSkills(): Promise<Skill[]> {
    return request<Skill[]>("/profile/skills");
  },

  async addSkill(name: string, level: number, category: string): Promise<Skill> {
    return request<Skill>("/profile/skills", {
      method: "POST",
      body: JSON.stringify({ name, level, category }),
    });
  },

  async deleteSkill(id: number): Promise<void> {
    return request<void>(`/profile/skills/${id}`, { method: "DELETE" });
  },

  async scan(role_text: string): Promise<ScanResult> {
    return request<ScanResult>("/scan", {
      method: "POST",
      body: JSON.stringify({ role_text }),
    });
  },

  async listApplicationsPage(page: number, pageSize: number): Promise<Page<Application>> {
    return request<Page<Application>>(`/applications?page=${page}&page_size=${pageSize}`);
  },

  async addApplication(
    company: string,
    role_title: string,
    match_score?: number
  ): Promise<Application> {
    return request<Application>("/applications", {
      method: "POST",
      body: JSON.stringify({ company, role_title, status: "applied", match_score }),
    });
  },
};
