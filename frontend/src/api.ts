import type {
  AlphaDetailResponse,
  FailurePatternResponse,
  OptionsResponse,
  OverviewResponse,
  PipelineEvent,
  PipelineRun,
  ResearchArtifact,
  SettingsResponse,
  SettingsTestResponse,
  TheoryEntry,
  TheoryUsageResponse,
} from './types'

const API_BASE = import.meta.env.VITE_API_BASE ?? '/api'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
    ...init,
  })
  if (!response.ok) {
    const text = await response.text()
    throw new Error(text || `Request failed: ${response.status}`)
  }
  return response.json() as Promise<T>
}

function query(params: Record<string, string | number | boolean | undefined | null>): string {
  const search = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') return
    search.set(key, String(value))
  })
  const text = search.toString()
  return text ? `?${text}` : ''
}

export const api = {
  getHealth: () => request<{ status: string }>('/health'),
  getOverview: () => request<OverviewResponse>('/overview'),
  getOptions: () => request<OptionsResponse>('/options'),
  getPipelineRuns: (limit = 20) => request<{ items: PipelineRun[] }>(`/pipeline/runs${query({ limit })}`),
  getPipelineRunEvents: (runId: string, limit = 120) =>
    request<{ items: PipelineEvent[] }>(`/pipeline/runs/${runId}/events${query({ limit })}`),
  getPipelineRunResearch: (runId: string, limit = 40) =>
    request<{ items: ResearchArtifact[] }>(`/pipeline/runs/${runId}/research${query({ limit })}`),
  getAlphas: (params: Record<string, string | number | boolean | undefined | null>) =>
    request<{ items: Array<Record<string, unknown>>; summary: Record<string, unknown>; correlation_matrix: Array<Record<string, unknown>> }>(
      `/alphas${query(params)}`,
    ),
  getAlphaDetail: (alphaId: string) => request<AlphaDetailResponse>(`/alphas/${alphaId}`),
  getFailurePatterns: (limit = 400) => request<FailurePatternResponse>(`/analytics/failure-patterns${query({ limit })}`),
  getResearch: (runId?: string) => request<Record<string, unknown>>(`/research${query({ run_id: runId })}`),
  getLogs: (path?: string) => request<Record<string, unknown>>(`/logs${query({ path })}`),
  getSettings: () => request<SettingsResponse>('/settings'),
  saveSettings: (payload: Record<string, unknown>) =>
    request<{ status: string; message: string }>('/settings', { method: 'POST', body: JSON.stringify(payload) }),
  testSettingsConnection: (payload: Record<string, unknown>) =>
    request<SettingsTestResponse>('/settings/test', { method: 'POST', body: JSON.stringify(payload) }),
  startRun: (payload: Record<string, unknown>) =>
    request<Record<string, unknown>>('/actions/run', { method: 'POST', body: JSON.stringify(payload) }),
  stopRun: () => request<Record<string, unknown>>('/actions/stop', { method: 'POST' }),
  getTheories: (params: Record<string, string | number | boolean | undefined | null>) =>
    request<{ items: TheoryEntry[]; summary: Array<{ domain: string; count: number }> }>(`/theories${query(params)}`),
  getTheoryUsage: (limit = 400) => request<TheoryUsageResponse>(`/theories/usage${query({ limit })}`),
  saveTheory: (payload: Record<string, unknown>) =>
    request<{ status: string; theory_id: string }>('/theories', { method: 'POST', body: JSON.stringify(payload) }),
  getStudioContext: (payload: Record<string, unknown>) =>
    request<Record<string, string>>('/studio/context', { method: 'POST', body: JSON.stringify(payload) }),
  studioQuery: (payload: Record<string, unknown>) =>
    request<Record<string, unknown>>('/studio/query', { method: 'POST', body: JSON.stringify(payload) }),
  studioGenerate: (payload: Record<string, unknown>) =>
    request<Record<string, unknown>>('/studio/generate', { method: 'POST', body: JSON.stringify(payload) }),
  studioSimulate: (payload: Record<string, unknown>) =>
    request<Record<string, unknown>>('/studio/simulate', { method: 'POST', body: JSON.stringify(payload) }),
  getChatMessages: (session = 'studio', limit = 60) =>
    request<{ items: Array<Record<string, unknown>> }>(`/chat/messages?session=${session}&limit=${limit}`),
  postChatMessage: (payload: Record<string, unknown>) =>
    request<Record<string, unknown>>('/chat/messages', { method: 'POST', body: JSON.stringify(payload) }),
  clearChatMessages: (session = 'studio') =>
    request<{ status: string }>(`/chat/messages?session=${session}`, { method: 'DELETE' }),
}
