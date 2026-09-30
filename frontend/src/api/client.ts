import type { ApiErrorBody } from './types'

const API_BASE = '/api/v1'
const TOKEN_KEY = 'copilot_access_token'

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY)
}

function extractMessage(body: unknown, fallback: string): string {
  const detail = (body as ApiErrorBody | null)?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail.length > 0) return detail[0].msg
  return (body as ApiErrorBody | null)?.title ?? fallback
}

async function request<T>(
  path: string,
  options: { method?: string; body?: unknown; auth?: boolean; query?: Record<string, string> } = {},
): Promise<T> {
  const { method = 'GET', body, auth = true, query } = options
  const headers: Record<string, string> = {}
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  if (auth) {
    const token = getToken()
    if (token) headers['Authorization'] = `Bearer ${token}`
  }

  const search = query ? `?${new URLSearchParams(query).toString()}` : ''
  const response = await fetch(API_BASE + path + search, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })

  if (response.status === 401) {
    clearToken()
  }

  if (!response.ok) {
    let parsed: unknown = null
    try {
      parsed = await response.json()
    } catch {
      // non-JSON error body; fall through to the generic message
    }
    throw new ApiError(response.status, extractMessage(parsed, `Request failed (${response.status})`))
  }

  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}

export const api = {
  get: <T>(path: string, query?: Record<string, string>) => request<T>(path, { query }),
  post: <T>(path: string, body?: unknown, query?: Record<string, string>) =>
    request<T>(path, { method: 'POST', body, query }),
  postNoAuth: <T>(path: string, body?: unknown) => request<T>(path, { method: 'POST', body, auth: false }),
}
