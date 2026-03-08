import client from './client'
import type { ShortlistEntry, ShortlistList, ShortlistStatus, PaginatedResponse, Profile, InterestList } from '@/types'

export const shortlistApi = {
  /** Express interest in a profile */
  create(to_profile_id: string, note?: string): Promise<ShortlistEntry> {
    return client.post('/shortlists/', { to_profile_id, note: note ?? null }).then((r) => r.data)
  },

  /** Fetch all shortlist entries sent by the current user (up to limit) */
  sent(limit = 500): Promise<ShortlistList> {
    return client.get('/shortlists/sent', { params: { skip: 0, limit } }).then((r) => r.data)
  },

  /** Withdraw interest by shortlist entry ID */
  delete(id: string): Promise<void> {
    return client.delete(`/shortlists/${id}`).then(() => undefined)
  },

  /** Remove a shortlist entry by the target profile's ID */
  deleteByProfile(toProfileId: string): Promise<void> {
    return client.delete(`/shortlists/by-profile/${toProfileId}`).then(() => undefined)
  },

  /** Browse shortlisted profiles – same paginated response shape as GET /profiles/ */
  shortlistedProfiles(page = 1, size = 12): Promise<PaginatedResponse<Profile>> {
    return client
      .get('/shortlists/shortlisted-profiles', { params: { page, size } })
      .then((r) => r.data)
  },

  /**
   * Sent interests with full recipient profile + status.
   * Used in "My Interests → Sent" tab.
   */
  sentInterests(page = 1, size = 20): Promise<InterestList> {
    return client
      .get('/shortlists/sent-interests', { params: { page, size } })
      .then((r) => r.data)
  },

  /**
   * Received interests with full sender profile + status.
   * Used in "My Interests → Received" tab.
   */
  receivedInterests(page = 1, size = 20, status?: string): Promise<InterestList> {
    return client
      .get('/shortlists/received-interests', {
        params: { page, size, ...(status ? { status } : {}) },
      })
      .then((r) => r.data)
  },

  /**
   * Accept or reject a received interest.
   * Only the recipient can call this.
   */
  respond(shortlistId: string, status: 'accepted' | 'rejected'): Promise<ShortlistEntry> {
    return client
      .patch(`/shortlists/${shortlistId}`, { status })
      .then((r) => r.data)
  },
}
