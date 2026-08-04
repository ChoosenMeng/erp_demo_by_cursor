/** Auth + entity (company) context. Entity selection outranks module navigation. */

import { computed, ref } from 'vue'
import {
  apiGet,
  apiPost,
  clearAuth,
  getAccessToken,
  getCompanyId,
  setCompanyId,
  setTokens,
} from '../api/client'

export type CompanyBrief = {
  id: number
  code: string
  name: string
  base_currency_code: string
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

/** Persisted entity id from localStorage (source of truth). */
export function getPreferredCompanyId(): number | null {
  const raw = getCompanyId()
  if (raw == null || raw === '') return null
  const n = Number(raw)
  return Number.isFinite(n) && n > 0 ? n : null
}

function companyAllowed(me: UserMe, companyId: number): boolean {
  return me.companies.some((c) => c.id === companyId)
}

/**
 * Bind profile to preferred entity. Never let a bare /me default overwrite
 * a valid persisted company selection (entity > function).
 */
function applyUser(me: UserMe, preferCompanyId?: number | null): void {
  const preferred = preferCompanyId ?? getPreferredCompanyId()
  let companyId = me.company_id

  if (preferred != null && companyAllowed(me, preferred)) {
    companyId = preferred
    setCompanyId(preferred)
  } else if (me.company_id != null) {
    setCompanyId(me.company_id)
    companyId = me.company_id
  }

  user.value = { ...me, company_id: companyId }
}

export function useAuthStore() {
  const isAuthenticated = computed(() => !!getAccessToken() && !!user.value)

  const companies = computed(() => user.value?.companies ?? [])

  const activeCompany = computed(() => {
    const id = user.value?.company_id ?? getPreferredCompanyId()
    if (id == null) return null
    return user.value?.companies.find((c) => c.id === id) ?? null
  })

  function hasPermission(code: string): boolean {
    const perms = user.value?.permissions ?? []
    return perms.includes('*') || perms.includes(code)
  }

  /** Re-assert entity context on every route change (entity > function). */
  function syncEntityContext(): void {
    if (!user.value) return
    const preferred = getPreferredCompanyId()
    if (preferred == null) {
      if (user.value.company_id != null) {
        setCompanyId(user.value.company_id)
      }
      return
    }
    if (!companyAllowed(user.value, preferred)) {
      // Saved entity no longer valid — fall back to server/default profile company
      const fallback =
        user.value.companies.find((c) => c.is_default)?.id ??
        user.value.companies[0]?.id ??
        null
      if (fallback != null) {
        setCompanyId(fallback)
        user.value = { ...user.value, company_id: fallback }
      }
      return
    }
    if (user.value.company_id !== preferred) {
      user.value = { ...user.value, company_id: preferred }
    }
    setCompanyId(preferred)
  }

  async function login(username: string, password: string): Promise<void> {
    const res = await apiPost<TokenPayload>(
      '/api/v1/auth/login',
      { username, password },
      false,
    )
    setTokens(res.data.access_token, res.data.refresh_token)
    // Fresh login: use server default entity (USCO)
    setCompanyId(res.data.user.company_id)
    applyUser(res.data.user, res.data.user.company_id)
  }

  async function fetchMe(): Promise<void> {
    if (!getAccessToken()) {
      user.value = null
      return
    }
    const preferred = getPreferredCompanyId()
    if (preferred != null) {
      setCompanyId(preferred)
    }
    const res = await apiGet<UserMe>('/api/v1/auth/me')
    applyUser(res.data, preferred)
  }

  async function switchCompany(companyId: number): Promise<void> {
    if (!user.value || !companyAllowed(user.value, companyId)) {
      throw new Error('无权切换到该公司（未关联或已停用）')
    }
    // Entity first: persist before any API / navigation
    setCompanyId(companyId)
    const res = await apiGet<UserMe>('/api/v1/auth/me')
    applyUser(res.data, companyId)
    if (user.value?.company_id !== companyId) {
      throw new Error(
        `公司切换未生效（期望 ${companyId}，实际 ${user.value?.company_id}）`,
      )
    }
  }

  async function bootstrap(): Promise<void> {
    if (bootstrapped.value) return
    try {
      const saved = getPreferredCompanyId()
      if (saved != null) {
        setCompanyId(saved)
      }
      await fetchMe()
      // Drop stale inactive entity ids (e.g. DEFAULT) left in localStorage
      syncEntityContext()
      const preferred = getPreferredCompanyId()
      if (
        preferred != null &&
        user.value != null &&
        !companyAllowed(user.value, preferred)
      ) {
        const fallback =
          user.value.companies.find((c) => c.is_default)?.id ??
          user.value.companies[0]?.id ??
          null
        setCompanyId(fallback)
        if (fallback != null) {
          user.value = { ...user.value, company_id: fallback }
        }
      }
    } catch {
      // Entity header may be stale/inactive; retry once with cleared entity
      try {
        setCompanyId(null)
        const res = await apiGet<UserMe>('/api/v1/auth/me')
        applyUser(res.data, res.data.company_id)
        syncEntityContext()
      } catch {
        clearAuth()
        user.value = null
      }
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
      // ignore
    } finally {
      clearAuth()
      user.value = null
    }
  }

  return {
    user,
    bootstrapped,
    isAuthenticated,
    companies,
    activeCompany,
    hasPermission,
    syncEntityContext,
    login,
    fetchMe,
    switchCompany,
    bootstrap,
    logout,
  }
}
