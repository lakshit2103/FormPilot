/**
 * Applications API client — all endpoints for the job search + form-filling workflow.
 */
import { apiClient } from './client';

export interface StartApplicationRequest {
  user_query: string;
}

export interface ApplicationSession {
  id: string;
  user_query: string;
  intent: Record<string, unknown> | null;
  company: string | null;
  role: string | null;
  location: string | null;
  status: string;
  current_node: string | null;
  created_at: string;
  updated_at: string;
}

export interface JobResult {
  id: string;
  title: string;
  company: string | null;
  location: string | null;
  url: string;
  domain: string | null;
  snippet: string | null;
  source_type: string;
  relevance_score: number;
  is_official: boolean;
  job_status: string;
}

export interface MissingQuestion {
  id: string;
  question: string;
  field_requirements: {
    type: string;
    hint: string;
    required: boolean;
    options: string[];
    constraints: Record<string, unknown>;
  };
  status: string;
}

export interface AnswerPayload {
  question_id: string;
  answer_value: string;
  save_to_profile: 'use_once' | 'save_to_profile' | 'replace_default';
}

export interface FieldMapping {
  id: string;
  profile_key: string | null;
  proposed_value: string | null;
  confidence: number | null;
  mapping_status: string;
  reason: string | null;
  user_approved: boolean;
}

export interface ReviewSummary {
  session_id: string;
  total_fields: number;
  auto_filled: number;
  user_provided: number;
  missing: number;
  low_confidence: number;
  errors: number;
  mappings: FieldMapping[];
  validation_errors: Array<{ id: string; error_type: string; error_message: string }>;
}

// ── Session Management ────────────────────────────────────────────────────────

export const applicationsApi = {
  start: (data: StartApplicationRequest) =>
    apiClient.post<ApplicationSession>('/api/applications/start', data).then(r => r.data),

  list: () =>
    apiClient.get<ApplicationSession[]>('/api/applications').then(r => r.data),

  get: (sessionId: string) =>
    apiClient.get<ApplicationSession>(`/api/applications/${sessionId}`).then(r => r.data),

  // Search
  triggerSearch: (sessionId: string) =>
    apiClient.post(`/api/applications/${sessionId}/search`).then(r => r.data),

  getJobs: (sessionId: string) =>
    apiClient.get<JobResult[]>(`/api/applications/${sessionId}/jobs`).then(r => r.data),

  selectJob: (sessionId: string, jobId: string) =>
    apiClient.post(`/api/applications/${sessionId}/select-job`, { job_id: jobId }).then(r => r.data),

  provideUrl: (sessionId: string, url: string) =>
    apiClient.post(`/api/applications/${sessionId}/job-url`, { url }).then(r => r.data),

  // Browser control
  continueSession: (sessionId: string) =>
    apiClient.post(`/api/applications/${sessionId}/continue`).then(r => r.data),

  stopSession: (sessionId: string) =>
    apiClient.post(`/api/applications/${sessionId}/stop`).then(r => r.data),

  getBrowserStatus: (sessionId: string) =>
    apiClient.get(`/api/applications/${sessionId}/browser-status`).then(r => r.data),

  // Missing questions
  getQuestions: (sessionId: string) =>
    apiClient.get<MissingQuestion[]>(`/api/applications/${sessionId}/questions`).then(r => r.data),

  submitAnswers: (sessionId: string, answers: AnswerPayload[]) =>
    apiClient.post(`/api/applications/${sessionId}/answers`, { answers }).then(r => r.data),

  // Review
  getReview: (sessionId: string) =>
    apiClient.get<ReviewSummary>(`/api/applications/${sessionId}/review`).then(r => r.data),

  editField: (sessionId: string, fieldId: string, value: string) =>
    apiClient.patch(`/api/applications/${sessionId}/fields/${fieldId}`, {
      proposed_value: value,
      user_approved: true,
    }).then(r => r.data),

  revalidate: (sessionId: string) =>
    apiClient.post(`/api/applications/${sessionId}/validate`).then(r => r.data),
};
