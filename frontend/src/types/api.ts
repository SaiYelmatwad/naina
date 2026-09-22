export interface User {
  id: number;
  email: string;
  full_name: string;
}

export interface Skill {
  id: number;
  name: string;
  level: number;
  category: string;
}

export interface SkillSignal {
  skill: string;
  level: number;
  weight: number;
}

export interface ScanResult {
  score: number;
  verdict: string;
  matched: SkillSignal[];
  gaps: SkillSignal[];
  explanation: string[];
}

export interface Application {
  id: number;
  company: string;
  role_title: string;
  status: string;
  match_score: number | null;
  created_at: string;
}
