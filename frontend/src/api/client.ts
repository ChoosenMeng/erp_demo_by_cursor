/** Lightweight API client with JWT + company header support. */

export type ApiResponse<T> = {
  code: number
  message: string
  data: T
}

const API_BASE = import.meta.env.VITE_API_BASE ?? ''
const ACCESS_KEY = 'erp_access_token'
const REFRESH_KEY = 'erp_refresh_token'
const COMPANY_KEY = 'erp_company_id'

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_KEY)
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_KEY)
}

export function getCompanyId(): string | null {
  return localStorage.getItem(COMPANY_KEY)
}

export function setTokens(access: string, refresh: string): void {
  localStorage.setItem(ACCESS_KEY, access)
  localStorage.setItem(REFRESH_KEY, refresh)
}

export function setCompanyId(companyId: number | null): void {
  if (companyId == null) {
    localStorage.removeItem(COMPANY_KEY)
    return
  }
  localStorage.setItem(COMPANY_KEY, String(companyId))
}

export function clearAuth(): void {
  localStorage.removeItem(ACCESS_KEY)
  localStorage.removeItem(REFRESH_KEY)
  localStorage.removeItem(COMPANY_KEY)
}

type RequestOptions = {
  method?: string
  body?: unknown
  auth?: boolean
  headers?: Record<string, string>
}

export async function apiRequest<T>(
  path: string,
  options: RequestOptions = {},
): Promise<ApiResponse<T>> {
  const headers: Record<string, string> = {
    ...(options.headers ?? {}),
  }

  if (options.body !== undefined) {
    headers['Content-Type'] = 'application/json'
  }

  if (options.auth !== false) {
    const token = getAccessToken()
    if (token) {
      headers.Authorization = `Bearer ${token}`
    }
    const companyId = getCompanyId()
    if (companyId) {
      headers['X-Company-Id'] = companyId
    }
  }

  const response = await fetch(`${API_BASE}${path}`, {
    method: options.method ?? (options.body !== undefined ? 'POST' : 'GET'),
    headers,
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
  })

  const payload = (await response.json()) as ApiResponse<T>
  if (!response.ok) {
    throw new Error(payload.message || `HTTP ${response.status}`)
  }
  return payload
}

export async function apiGet<T>(path: string, auth = true): Promise<ApiResponse<T>> {
  return apiRequest<T>(path, { method: 'GET', auth })
}

export async function apiPost<T>(
  path: string,
  body?: unknown,
  auth = true,
): Promise<ApiResponse<T>> {
  return apiRequest<T>(path, { method: 'POST', body, auth })
}

export async function apiPatch<T>(path: string, body: unknown): Promise<ApiResponse<T>> {
  return apiRequest<T>(path, { method: 'PATCH', body })
}

export async function apiPut<T>(path: string, body: unknown): Promise<ApiResponse<T>> {
  return apiRequest<T>(path, { method: 'PUT', body })
}
