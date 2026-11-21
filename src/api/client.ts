// ============================================================
// EXAMFLOW – Central Typed API Client
// ============================================================

import type {
  ApiResponse,
  PaginatedResponse,
  ApiError,
  DashboardStats,
  Examination,
  Candidate,
  CandidateResponses,
  EvaluationResult,
  ProctoringEvent,
  ShiftStatistics,
  MeritListEntry,
  Conversation,
  ChatMessage,
  Document,
  ReEvaluationRequest,
  User,
  Notification,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

// ── Helpers ──────────────────────────────────────────────────

class ApiClientError extends Error {
  status: number;
  code: string;
  details?: Record<string, string[]>;

  constructor(error: ApiError) {
    super(error.message);
    this.name = 'ApiClientError';
    this.status = error.status;
    this.code = error.code;
    this.details = error.details;
  }
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = localStorage.getItem('examflow_token');

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...((options.headers as Record<string, string>) || {}),
  };

  // Don't set Content-Type for FormData
  if (options.body instanceof FormData) {
    delete (headers as Record<string, string>)['Content-Type'];
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    localStorage.removeItem('examflow_token');
    window.dispatchEvent(new CustomEvent('auth:unauthorized'));
    throw new ApiClientError({
      message: 'Authentication required',
      code: 'UNAUTHORIZED',
      status: 401,
    });
  }

  if (!response.ok) {
    let errorBody: ApiError;
    try {
      errorBody = await response.json();
    } catch {
      errorBody = {
        message: response.statusText || 'Request failed',
        code: 'UNKNOWN',
        status: response.status,
      };
    }
    throw new ApiClientError(errorBody);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

// ── Auth ─────────────────────────────────────────────────────

export const authApi = {
  login(email: string, password: string) {
    return request<ApiResponse<{ user: User; token: string }>>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  },
  logout() {
    return request<void>('/auth/logout', { method: 'POST' });
  },
  me() {
    return request<ApiResponse<User>>('/auth/me');
  },
};

// ── Dashboard ────────────────────────────────────────────────

export const dashboardApi = {
  getStats() {
    return request<ApiResponse<DashboardStats>>('/dashboard/stats');
  },
};

// ── Examinations ─────────────────────────────────────────────

export const examinationApi = {
  list(params?: { page?: number; pageSize?: number; status?: string }) {
    const qs = new URLSearchParams();
    if (params?.page) qs.set('page', String(params.page));
    if (params?.pageSize) qs.set('pageSize', String(params.pageSize));
    if (params?.status) qs.set('status', params.status);
    return request<PaginatedResponse<Examination>>(`/examinations?${qs}`);
  },
  get(id: string) {
    return request<ApiResponse<Examination>>(`/examinations/${id}`);
  },
  create(data: Partial<Examination>) {
    return request<ApiResponse<Examination>>('/examinations', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
  update(id: string, data: Partial<Examination>) {
    return request<ApiResponse<Examination>>(`/examinations/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },
  delete(id: string) {
    return request<void>(`/examinations/${id}`, { method: 'DELETE' });
  },
};

// ── Candidates ───────────────────────────────────────────────

export const candidateApi = {
  list(params?: {
    page?: number;
    pageSize?: number;
    examinationId?: string;
    category?: string;
    status?: string;
    search?: string;
  }) {
    const qs = new URLSearchParams();
    if (params?.page) qs.set('page', String(params.page));
    if (params?.pageSize) qs.set('pageSize', String(params.pageSize));
    if (params?.examinationId) qs.set('examinationId', params.examinationId);
    if (params?.category) qs.set('category', params.category);
    if (params?.status) qs.set('status', params.status);
    if (params?.search) qs.set('search', params.search);
    return request<PaginatedResponse<Candidate>>(`/candidates?${qs}`);
  },
  get(id: string) {
    return request<ApiResponse<Candidate>>(`/candidates/${id}`);
  },
};

// ── Responses ────────────────────────────────────────────────

export const responseApi = {
  getCandidateResponses(candidateId: string, examinationId: string) {
    return request<ApiResponse<CandidateResponses>>(
      `/responses/${candidateId}/${examinationId}`
    );
  },
};

// ── Evaluation ───────────────────────────────────────────────

export const evaluationApi = {
  getResult(candidateId: string, examinationId: string) {
    return request<ApiResponse<EvaluationResult>>(
      `/evaluation/${candidateId}/${examinationId}`
    );
  },
  listResults(examinationId: string, params?: { page?: number; pageSize?: number }) {
    const qs = new URLSearchParams();
    if (params?.page) qs.set('page', String(params.page));
    if (params?.pageSize) qs.set('pageSize', String(params.pageSize));
    return request<PaginatedResponse<EvaluationResult>>(
      `/evaluation/examination/${examinationId}?${qs}`
    );
  },
  triggerEvaluation(examinationId: string) {
    return request<ApiResponse<{ jobId: string }>>(
      `/evaluation/trigger/${examinationId}`,
      { method: 'POST' }
    );
  },
};

// ── Proctoring ───────────────────────────────────────────────

export const proctoringApi = {
  getEvents(candidateId: string, examinationId: string) {
    return request<ApiResponse<ProctoringEvent[]>>(
      `/proctoring/${candidateId}/${examinationId}`
    );
  },
  listEvents(examinationId: string, params?: { severity?: string; page?: number }) {
    const qs = new URLSearchParams();
    if (params?.severity) qs.set('severity', params.severity);
    if (params?.page) qs.set('page', String(params.page));
    return request<PaginatedResponse<ProctoringEvent>>(
      `/proctoring/examination/${examinationId}?${qs}`
    );
  },
};

// ── Normalisation ────────────────────────────────────────────

export const normalisationApi = {
  getShiftStatistics(examinationId: string) {
    return request<ApiResponse<ShiftStatistics[]>>(
      `/normalisation/${examinationId}/statistics`
    );
  },
};

// ── Merit List ───────────────────────────────────────────────

export const meritListApi = {
  get(examinationId: string, params?: {
    page?: number;
    pageSize?: number;
    category?: string;
    search?: string;
  }) {
    const qs = new URLSearchParams();
    if (params?.page) qs.set('page', String(params.page));
    if (params?.pageSize) qs.set('pageSize', String(params.pageSize));
    if (params?.category) qs.set('category', params.category);
    if (params?.search) qs.set('search', params.search);
    return request<PaginatedResponse<MeritListEntry>>(
      `/merit-list/${examinationId}?${qs}`
    );
  },
};

// ── Re-evaluation ────────────────────────────────────────────

export const reEvaluationApi = {
  list(examinationId: string, params?: { page?: number; status?: string }) {
    const qs = new URLSearchParams();
    if (params?.page) qs.set('page', String(params.page));
    if (params?.status) qs.set('status', params.status);
    return request<PaginatedResponse<ReEvaluationRequest>>(
      `/re-evaluation/${examinationId}?${qs}`
    );
  },
  create(data: { candidateId: string; examinationId: string; reason: string }) {
    return request<ApiResponse<ReEvaluationRequest>>('/re-evaluation', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
  approve(id: string, remarks: string) {
    return request<ApiResponse<ReEvaluationRequest>>(
      `/re-evaluation/${id}/approve`,
      { method: 'POST', body: JSON.stringify({ remarks }) }
    );
  },
  reject(id: string, remarks: string) {
    return request<ApiResponse<ReEvaluationRequest>>(
      `/re-evaluation/${id}/reject`,
      { method: 'POST', body: JSON.stringify({ remarks }) }
    );
  },
};

// ── Chat / AI ────────────────────────────────────────────────

export const chatApi = {
  listConversations() {
    return request<ApiResponse<Conversation[]>>('/chat/conversations');
  },
  getConversation(id: string) {
    return request<ApiResponse<Conversation>>(`/chat/conversations/${id}`);
  },
  createConversation(title: string) {
    return request<ApiResponse<Conversation>>('/chat/conversations', {
      method: 'POST',
      body: JSON.stringify({ title }),
    });
  },
  sendMessage(conversationId: string, content: string, attachments?: string[]) {
    return request<ApiResponse<ChatMessage>>(
      `/chat/conversations/${conversationId}/messages`,
      {
        method: 'POST',
        body: JSON.stringify({ content, attachments }),
      }
    );
  },
  uploadDocument(file: File) {
    const formData = new FormData();
    formData.append('file', file);
    return request<ApiResponse<Document>>('/chat/documents', {
      method: 'POST',
      body: formData,
    });
  },
  deleteConversation(id: string) {
    return request<void>(`/chat/conversations/${id}`, { method: 'DELETE' });
  },
  streamMessage(conversationId: string, content: string, attachments?: string[]) {
    const token = localStorage.getItem('examflow_token');
    return fetch(`${API_BASE_URL}/chat/conversations/${conversationId}/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ content, attachments }),
    });
  },
};

// ── Notifications ────────────────────────────────────────────

export const notificationApi = {
  list() {
    return request<ApiResponse<Notification[]>>('/notifications');
  },
  markRead(id: string) {
    return request<void>(`/notifications/${id}/read`, { method: 'POST' });
  },
  markAllRead() {
    return request<void>('/notifications/read-all', { method: 'POST' });
  },
};

export { ApiClientError };
