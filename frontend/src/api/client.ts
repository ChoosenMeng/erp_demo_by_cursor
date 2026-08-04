export type ApiResponse<T> = {
  code: number
  message: string
  data: T
}

const API_BASE = import.meta.env.VITE_API_BASE ?? ''

export async function apiGet<T>(path: string): Promise<ApiResponse<T>> {
  const response = await fetch(`${API_BASE}${path}`)
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return response.json() as Promise<ApiResponse<T>>
}
