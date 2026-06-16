import axios from "axios";

const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: apiBaseUrl,
});

// Add authorization header from localStorage
api.interceptors.request.use((config) => {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Types
export interface CaseSearchResult {
  id: string;
  case_number?: string;
  citation?: string;
  title: string;
  court_name?: string;
  judge_name?: string;
  date_decided?: string;
  practice_area: string;
  outcome: string;
  language: string;
  snippet?: string;
}

export interface JudgeProfileData {
  total_decisions: number;
  plaintiff_favourable_rate?: number;
  avg_disposal_days?: number;
  interlocutory_grant_rate?: number;
  costs_awarded_rate?: number;
  top_practice_areas?: string;
}

export interface Judge {
  id: string;
  name: string;
  state?: string;
  court_name?: string;
  court_type?: string;
  profile?: JudgeProfileData;
}

// API Functions
export async function searchCases(params: {
  q?: string;
  court_type?: string;
  state?: string;
  year_from?: number;
  year_to?: number;
  practice_area?: string;
  outcome?: string;
  language?: string;
  limit?: number;
  offset?: number;
}) {
  const { data } = await api.get<CaseSearchResult[]>("/cases/search", { params });
  return data;
}

export async function getJudge(id: string) {
  const { data } = await api.get<Judge>(`/judges/${id}`);
  return data;
}

export async function getJudgeAnalytics(id: string) {
  const { data } = await api.get<JudgeProfileData>(`/judges/${id}/analytics`);
  return data;
}

export async function getJudgeCases(
  id: string,
  params?: {
    year_from?: number;
    year_to?: number;
    practice_area?: string;
    outcome?: string;
    limit?: number;
    offset?: number;
  }
) {
  const { data } = await api.get(`/judges/${id}/cases`, { params });
  return data;
}

export async function summariseCase(caseId: string) {
  const { data } = await api.post("/ai/summarise", { case_id: caseId });
  return data;
}

export async function assessCase(facts: string, claim_type: string, court: string) {
  const { data } = await api.post("/ai/assess", {
    facts,
    claim_type,
    court,
  });
  return data;
}

export async function draftDocument(doc_type: string, facts: string, language: string) {
  const { data } = await api.post("/ai/draft", {
    doc_type,
    facts,
    language,
  });
  return data;
}

export default api;
