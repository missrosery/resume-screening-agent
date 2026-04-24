import { InterviewQuestionGroup, Position, Resume, RankedResume, Session } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    cache: "no-store",
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed: ${response.status}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export const api = {
  listPositions: () => request<Position[]>("/positions"),
  createPosition: (payload: { title: string; department?: string; requirements?: string }) =>
    request<Position>("/positions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  getPosition: (positionId: string) => request<Position>(`/positions/${positionId}`),
  deletePosition: (positionId: string) =>
    request<void>(`/positions/${positionId}`, {
      method: "DELETE",
    }),
  getResume: (resumeId: string) => request<Resume>(`/resumes/${resumeId}`),
  uploadResumes: async (positionId: string, files: File[]) => {
    const form = new FormData();
    files.forEach((file) => form.append("files", file));
    const response = await fetch(`${API_URL}/positions/${positionId}/resumes/upload`, {
      method: "POST",
      body: form,
    });
    if (!response.ok) {
      throw new Error(await response.text());
    }
    return response.json() as Promise<Resume[]>;
  },
  listResumes: (positionId: string) => request<Resume[]>(`/positions/${positionId}/resumes`),
  deleteResume: (resumeId: string) =>
    request<void>(`/resumes/${resumeId}`, {
      method: "DELETE",
    }),
  screenPosition: (positionId: string, payload: { query: string; top_n?: number }) =>
    request<{ items: RankedResume[] }>(`/positions/${positionId}/screen`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  createSession: (positionId: string, title: string) =>
    request<Session>(`/positions/${positionId}/sessions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title }),
    }),
  compareResumes: (resume_id_a: string, resume_id_b: string, criteria?: string) =>
    request<{ summary: string }>("/resumes/compare", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ resume_id_a, resume_id_b, criteria }),
    }),
  interviewQuestions: (resumeId: string) =>
    request<{ questions: string[]; groups: InterviewQuestionGroup[] }>(`/resumes/${resumeId}/interview-questions`, {
      method: "POST",
    }),
  apiUrl: API_URL,
};
