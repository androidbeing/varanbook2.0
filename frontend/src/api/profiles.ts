import client from './client'
import type { Profile, PaginatedResponse } from '@/types'

export interface ProfilesQuery {
  page?: number
  size?: number
  gender?: string
  city?: string
  min_age?: number
  max_age?: number
  search?: string
}

export const profilesApi = {
  list(params: ProfilesQuery = {}): Promise<PaginatedResponse<Profile>> {
    return client.get('/profiles', { params }).then((r) => r.data)
  },

  get(id: string): Promise<Profile> {
    return client.get(`/profiles/${id}`).then((r) => r.data)
  },

  mine(): Promise<Profile> {
    return client.get('/profiles/me').then((r) => r.data)
  },

  create(data: Partial<Profile>): Promise<Profile> {
    return client.post('/profiles', data).then((r) => r.data)
  },

  update(id: string, data: Partial<Profile>): Promise<Profile> {
    return client.patch(`/profiles/${id}`, data).then((r) => r.data)
  },

  uploadPhoto(id: string, file: File): Promise<{ url: string }> {
    const form = new FormData()
    form.append('file', file)
    return client
      .post(`/profiles/${id}/photo`, form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      .then((r) => r.data)
  },
}
