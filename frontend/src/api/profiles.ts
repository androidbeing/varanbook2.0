import client from './client'
import type { Profile, PartnerPreference, PaginatedResponse } from '@/types'

export interface ProfilesQuery {
  page?: number
  size?: number
  gender?: string
  status?: string
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

  setStatus(profileId: string, status: 'active' | 'suspended' | 'matched'): Promise<Profile> {
    return client.patch(`/profiles/${profileId}/status`, { status }).then((r) => r.data)
  },

  delete(profileId: string): Promise<void> {
    return client.delete(`/profiles/${profileId}`).then(() => undefined)
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

export const filesApi = {
  /** Get a short-lived presigned GET URL to display a private S3 object. */
  presignGet(key: string): Promise<{ url: string; expires_in: number }> {
    return client.get('/files/presign-get', { params: { key } }).then((r) => r.data)
  },

  /** Get a presigned PUT URL for an avatar (user profile picture). */
  presignAvatar(data: {
    file_name: string
    content_type: string
    purpose?: 'avatar' | 'tenant_logo' | 'upi_qr'
  }): Promise<{ upload_url: string; object_key: string }> {
    return client.post('/files/avatar/presign', { purpose: 'avatar', ...data }).then((r) => r.data)
  },

  /** Register the uploaded avatar key on the authenticated user. */
  registerAvatar(object_key: string): Promise<void> {
    return client.patch('/files/users/me/avatar', null, { params: { object_key } }).then(() => undefined)
  },

  /** Register the uploaded logo key on the current tenant. */
  registerTenantLogo(object_key: string): Promise<void> {
    return client.patch('/files/tenant/logo', null, { params: { object_key } }).then(() => undefined)
  },

  /** Register the uploaded UPI QR key on the current tenant. */
  registerTenantUpiQr(object_key: string): Promise<void> {
    return client.patch('/files/tenant/upi-qr', null, { params: { object_key } }).then(() => undefined)
  },

  /** Delete a photo from a profile (removes from S3 and deregisters the key). */
  deletePhoto(profileId: string, object_key: string): Promise<void> {
    return client
      .delete(`/files/profiles/${profileId}/photos`, { params: { object_key } })
      .then(() => undefined)
  },

  /**
   * Upload a file directly to S3 using a presigned PUT URL.
   * Should be called after obtaining the URL from presignAvatar / presign.
   *
   * Throws an Error whose message describes the failure:
   *  - "S3 upload failed: 403 Forbidden" for permission / CORS errors
   *  - "S3 upload failed: Failed to fetch" when the request is blocked by
   *    the browser (e.g. missing S3 CORS configuration)
   */
  async putToS3(uploadUrl: string, file: File): Promise<void> {
    let res: Response
    try {
      res = await fetch(uploadUrl, {
        method: 'PUT',
        body: file,
        headers: { 'Content-Type': file.type },
      })
    } catch (networkErr: any) {
      // Browser blocked the request (CORS preflight failed, offline, etc.)
      const reason = networkErr?.message ?? 'Network error'
      throw new Error(
        `S3 upload blocked by browser: ${reason}. ` +
        'Ensure the S3 bucket CORS policy allows PUT from this origin.',
      )
    }
    if (!res.ok) {
      throw new Error(`S3 upload failed: ${res.status} ${res.statusText}`)
    }
  },
}
