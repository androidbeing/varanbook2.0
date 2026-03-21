import client from './client'

export interface CasteLockStatus {
  caste_locked: boolean
}

export const castesApi = {
  /** List castes configured for the current user's tenant. */
  list(): Promise<string[]> {
    return client.get('/castes/').then((r) => r.data)
  },

  /** Replace the entire caste list (admin only). */
  replace(castes: string[]): Promise<string[]> {
    return client.put('/castes/', castes).then((r) => r.data)
  },

  /** Add a single caste (admin only). */
  add(caste: string): Promise<string[]> {
    return client.post('/castes/', null, { params: { caste } }).then((r) => r.data)
  },

  /** Remove a single caste (admin only). */
  remove(caste: string): Promise<string[]> {
    return client.delete(`/castes/${encodeURIComponent(caste)}`).then((r) => r.data)
  },

  /** Get caste lock status for the current tenant. */
  getLockStatus(): Promise<CasteLockStatus> {
    return client.get('/castes/lock-status').then((r) => r.data)
  },

  /** Set caste lock status (admin only). */
  setLockStatus(locked: boolean): Promise<CasteLockStatus> {
    return client.put('/castes/lock-status', { caste_locked: locked }).then((r) => r.data)
  },
}
