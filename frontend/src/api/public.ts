/**
 * API client for unauthenticated public endpoints (self-registration).
 * Uses a plain axios instance without JWT or tenant-ID interceptors.
 */
import axios from 'axios'
import type { TenantPublicInfo, SelfRegisterPayload, SelfRegistrationStatus, User } from '@/types'

const BASE_URL =
  import.meta.env.VITE_API_BASE_URL ??
  `${window.location.protocol}//${window.location.hostname}:8000`

const publicClient = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
})

export const publicApi = {
  /** Fetch minimal tenant info for the /join page. */
  async getTenant(slug: string): Promise<TenantPublicInfo> {
    const { data } = await publicClient.get<TenantPublicInfo>(`/public/tenant/${encodeURIComponent(slug)}`)
    return data
  },

  /** Self-register a new member under the given tenant. */
  async register(slug: string, payload: SelfRegisterPayload): Promise<User> {
    const { data } = await publicClient.post<User>(`/public/register/${encodeURIComponent(slug)}`, payload)
    return data
  },
}

export default publicApi
