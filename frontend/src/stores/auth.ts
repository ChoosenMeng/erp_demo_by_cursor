/** Simple auth state helpers backed by localStorage + /auth/me. */

import { computed, ref } from 'vue'
import {
  apiGet,
  apiPost,
  clearAuth,
  getAccessToken,
  setCompanyId,
  setTokens,
} from '../api/client'

export type CompanyBrief = {
  id: number
  code: string
  name: string
  is_default: boolean
}

export type UserMe = {
  id: number
  username: string
  display_name: string
  roles: string[]
  permissions: string[]
  companies: CompanyBrief[]
  company_id: number | null
}

export type TokenPayload = {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: UserMe
}

const user = ref<UserMe | null>(null)
const bootstrapped = ref(false)

export function useAuthStore() {
  const isAuthenticated = computed(() => !!getAccessToken() && !!user.value)

  function hasPermission(code: string): boolean {
    const perms = user.value?.permissions ?? []
    return perms.includes('*') || perms.includes(code)
  }

  async function login(username: string, password: string): Promise<void> {
    const res = await apiPost<TokenPayload>(
      '/api/v1/auth/login',
      { username, password },
      false,
    )
    setTokens(res.data.access_token, res.data.refresh_token)
    user.value = res.data.user
    setCompanyId(res.data.user.company_id)
  }

  async function fetchMe(): Promise<void> {
    if (!getAccessToken()) {
      user.value = null
      return
    }
    const res = await apiGet<UserMe>('/api/v1/auth/me')
    user.value = res.data
    setCompanyId(res.data.company_id)
  }

  async function bootstrap(): Promise<void> {
    if (bootstrapped.value) return
    try {
      await fetchMe()
    } catch {
      clearAuth()
      user.value = null
    } finally {
      bootstrapped.value = true
    }
  }

  async function logout(): Promise<void> {
    try {
      if (getAccessToken()) {
        await apiPost('/api/v1/auth/logout', {})
      }
    } catch {
      // ignore network errors on logout
    } finally {
      clearAuth()
      user.value = null
    }
  }

  return {
    user,
    bootstrapped,
    isAuthenticated,
    hasPermission,
    login,
    fetchMe,
    bootstrap,
    logout,
  }
}
