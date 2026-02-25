// ── Auth ────────────────────────────────────────────────────────────────────
export interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface LoginPayload {
  email: string
  password: string
}

// ── User ────────────────────────────────────────────────────────────────────
export type UserRole = 'super_admin' | 'admin' | 'member'

export interface User {
  id: string
  email: string
  name: string
  role: UserRole
  is_active: boolean
  tenant_id: string | null
  created_at: string
  updated_at: string
}

// ── Profile ─────────────────────────────────────────────────────────────────
export type Gender = 'male' | 'female' | 'other'
export type MaritalStatus = 'never_married' | 'divorced' | 'widowed' | 'annulled'
export type ProfileStatus = 'draft' | 'pending' | 'active' | 'hidden' | 'banned'

export interface Profile {
  id: string
  user_id: string
  display_name: string
  date_of_birth: string | null
  gender: Gender | null
  marital_status: MaritalStatus | null
  religion: string | null
  caste: string | null
  sub_caste: string | null
  mother_tongue: string | null
  city: string | null
  state: string | null
  country: string | null
  height_cm: number | null
  weight_kg: number | null
  complexion: string | null
  qualification: string | null
  occupation: string | null
  income_range: string | null
  about_me: string | null
  partner_preferences: string | null
  profile_photo_url: string | null
  status: ProfileStatus
  created_at: string
  updated_at: string
}

export interface ProfileListItem {
  id: string
  display_name: string
  date_of_birth: string | null
  gender: Gender | null
  city: string | null
  state: string | null
  profession: string | null
  profile_photo_url: string | null
  status: ProfileStatus
}

// ── Pagination ───────────────────────────────────────────────────────────────
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}

// ── API Error ────────────────────────────────────────────────────────────────
export interface ApiError {
  detail: string | { msg: string; type: string }[]
}
