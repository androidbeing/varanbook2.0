import client from './client'
import type { Profile, PartnerPreference, PaginatedResponse } from '@/types'

export interface ProfilesQuery {
  page?: number
  size?: number
  gender?: string
  city?: string
  dhosam?: string
  min_age?: number
  max_age?: number
  search?: string
}

export interface PresignRequest {
  file_name: string
  content_type: string
  upload_purpose: 'profile_photo' | 'horoscope'
}

export interface PresignResponse {
  upload_url: string
  object_key: string
}

export const profilesApi = {
  list(params: ProfilesQuery = {}): Promise<PaginatedResponse<Profile>> {
    return client.get('/profiles/', { params }).then((r) => r.data)
  },

  get(id: string): Promise<Profile> {
    return client.get(`/profiles/${id}`).then((r) => r.data)
  },

  mine(): Promise<Profile> {
    return client.get('/profiles/me').then((r) => r.data)
  },

  updateMe(data: Partial<Profile>): Promise<Profile> {
    return client.patch('/profiles/me', data).then((r) => r.data)
  },

  create(data: Partial<Profile>): Promise<Profile> {
    return client.post('/profiles/', data).then((r) => r.data)
  },

  update(id: string, data: Partial<Profile>): Promise<Profile> {
    return client.patch(`/profiles/${id}`, data).then((r) => r.data)
  },

  presign(data: PresignRequest): Promise<PresignResponse> {
    return client.post('/files/presign', data).then((r) => r.data)
  },

  registerMedia(profileId: string, objectKey: string, purpose: string): Promise<void> {
    return client
      .patch(`/files/profiles/${profileId}/media`, null, {
        params: { object_key: objectKey, purpose },
      })
      .then(() => undefined)
  },
}

export const preferencesApi = {
  get(profileId: string): Promise<PartnerPreference> {
    return client.get(`/profiles/${profileId}/preferences`).then((r) => r.data)
  },

  upsert(profileId: string, data: Partial<PartnerPreference>): Promise<PartnerPreference> {
    return client.put(`/profiles/${profileId}/preferences`, data).then((r) => r.data)
  },
}

export const usersApi = {
  updateMe(data: { full_name?: string; phone?: string }): Promise<void> {
    return client.patch('/users/me', data).then(() => undefined)
  },
}
