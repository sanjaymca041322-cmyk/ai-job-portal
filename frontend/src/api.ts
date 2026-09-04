export type Candidate = {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  phone: string | null;
  location: string | null;
  skills: string | null;
  experience_years: number | null;
  education: string | null;
  resume_filename: string | null;
  resume_path: string | null;
  created_at: string;
  updated_at: string;
};

export type Job = {
  id: string;
  title: string;
  description: string;
  required_skills: string;
  preferred_skills: string | null;
  minimum_experience_years: number;
  maximum_experience_years: number | null;
  education: string | null;
  location: string | null;
  employment_type: string;
  salary_min: number | null;
  salary_max: number | null;
  status: string;
  created_at: string;
  updated_at: string;
};

export type Match = {
  candidate_id: string;
  candidate_name: string;
  match_score: number;
  matching_skills: string[];
  missing_skills: string[];
  experience_match?: boolean;
  education_match?: boolean;
  explanation?: string;
};

export type ParsedResume = {
  name: string | null;
  email: string | null;
  phone: string | null;
  location: string | null;
  skills: string[];
  education: string | null;
  experience_years: number | null;
  work_experience: string[];
  certifications: string[];
  projects: string[];
  summary: string | null;
};

const API_URL = (import.meta.env.VITE_API_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, options);
  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      detail = body.detail || detail;
    } catch { /* response may not be JSON */ }
    throw new Error(detail);
  }
  return response.json() as Promise<T>;
}

export const api = {
  candidates: () => request<Candidate[]>("/candidates"),
  candidate: (id: string) => request<Candidate>(`/candidates/${id}`),
  createCandidate: (payload: Record<string, unknown>) => request<Candidate>("/candidates", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }),
  uploadResume: (id: string, file: File) => { const form = new FormData(); form.append("file", file); return request<Candidate>(`/candidates/${id}/resume`, { method: "POST", body: form }); },
  parseResume: (id: string) => request<ParsedResume>(`/candidates/${id}/resume/parse`, { method: "POST" }),
  jobs: () => request<Job[]>("/jobs"),
  job: (id: string) => request<Job>(`/jobs/${id}`),
  createJob: (payload: Record<string, unknown>) => request<Job>("/jobs", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }),
  updateJob: (id: string, payload: Record<string, unknown>) => request<Job>(`/jobs/${id}`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }),
  matches: (id: string) => request<Match[]>(`/jobs/${id}/matches`),
};
