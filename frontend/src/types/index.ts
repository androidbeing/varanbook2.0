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
  full_name: string
  role: UserRole
  is_active: boolean
  tenant_id: string | null
  created_at: string
  updated_at: string
}

// ── Enums ────────────────────────────────────────────────────────────────────
export type Gender = 'male' | 'female' | 'other'
export type MaritalStatus = 'never_married' | 'divorced' | 'widowed' | 'awaiting_divorce'
export type ProfileStatus = 'draft' | 'active' | 'suspended' | 'matched'
export type Rashi = 'mesha' | 'vrishabha' | 'mithuna' | 'karka' | 'simha' | 'kanya' | 'tula' | 'vrishchika' | 'dhanu' | 'makara' | 'kumbha' | 'meena'
export type Star = 'ashwini' | 'bharani' | 'krittika' | 'rohini' | 'mrigashira' | 'ardra' | 'punarvasu' | 'pushya' | 'ashlesha' | 'magha' | 'purva_phalguni' | 'uttara_phalguni' | 'hasta' | 'chitra' | 'swati' | 'vishakha' | 'anuradha' | 'jyeshtha' | 'moola' | 'purva_ashadha' | 'uttara_ashadha' | 'shravana' | 'dhanishtha' | 'shatabhisha' | 'purva_bhadrapada' | 'uttara_bhadrapada' | 'revati'
export type Dhosam = 'none' | 'chevvai' | 'rahu' | 'kethu' | 'shani' | 'multiple'
export type Qualification = 'below_10th' | 'sslc' | 'hsc' | 'diploma' | 'bachelor' | 'master' | 'doctorate' | 'professional' | 'other'
export type IncomeRange = 'below_2l' | '2_to_5l' | '5_to_10l' | '10_to_20l' | '20_to_50l' | 'above_50l'

// ── Profile ─────────────────────────────────────────────────────────────────
export interface Profile {
  id: string
  user_id: string
  tenant_id: string

  // Personal
  gender: Gender | null
  date_of_birth: string | null
  time_of_birth: string | null
  height_cm: number | null
  weight_kg: number | null
  complexion: string | null
  blood_group: string | null
  marital_status: MaritalStatus | null
  disabilities: string | null

  // Religious / cultural
  religion: string | null
  caste: string | null
  sub_caste: string | null
  gotra: string | null
  mother_tongue: string | null

  // Horoscope / birth
  birth_place: string | null
  rashi: Rashi | null
  star: Star | null
  dhosam: Dhosam | null
  manglik: boolean | null
  horoscope_key: string | null

  // Professional
  qualification: Qualification | null
  profession: string | null
  working_at: string | null
  income_range: IncomeRange | null

  // Location
  city: string | null
  state: string | null
  country: string | null
  native_place: string | null
  current_location: string | null

  // Family
  father_name: string | null
  father_occupation: string | null
  mother_name: string | null
  mother_occupation: string | null
  siblings_details: string | null

  // Contact
  mobile: string | null
  whatsapp: string | null

  // Photos
  photo_keys: string[] | null

  // Privacy
  personal_visible: boolean
  photo_visible: boolean
  birth_visible: boolean
  professional_visible: boolean
  family_visible: boolean
  contact_visible: boolean
  horoscope_visible: boolean

  // Status & audit
  status: ProfileStatus
  created_at: string
  updated_at: string

  // Derived from user (populated by backend)
  full_name?: string | null
}

// ── Partner Preference ───────────────────────────────────────────────────────
export interface PartnerPreference {
  id: string
  profile_id: string
  age_min: number | null
  age_max: number | null
  height_min_cm: number | null
  height_max_cm: number | null
  weight_min_kg: number | null
  weight_max_kg: number | null
  qualifications: Qualification[]
  income_ranges: IncomeRange[]
  marital_statuses: MaritalStatus[]
  current_locations: string[]
  native_locations: string[]
  castes: string[]
  religions: string[]
  dhosam: Dhosam[]
  rashi: Rashi[]
  star: Star[]
  updated_at: string
}

export interface ProfileListItem {
  id: string
  user_id: string
  gender: Gender | null
  date_of_birth: string | null
  city: string | null
  state: string | null
  profession: string | null
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

// ── Tenant ───────────────────────────────────────────────────────────────────
export type TenantPlan = 'starter' | 'growth' | 'enterprise'

export interface Tenant {
  id: string
  name: string
  slug: string
  domain: string | null
  contact_email: string
  plan: TenantPlan
  max_users: number
  max_admins: number
  is_active: boolean
  contact_person: string | null
  contact_number: string | null
  whatsapp_number: string | null
  pin: string | null
  upi_id: string | null
  castes: string[] | null
  created_at: string
  updated_at: string
}

export interface TenantCreate {
  name: string
  slug: string
  domain?: string | null
  contact_email: string
  address?: string | null
  plan: TenantPlan
  max_users: number
  max_admins: number
  contact_person: string
  contact_number: string
  whatsapp_number?: string | null
  pin: string
  upi_id?: string | null
  castes?: string[]
}

export interface TenantUpdate {
  name?: string
  domain?: string | null
  contact_email?: string
  address?: string | null
  plan?: TenantPlan
  max_users?: number
  max_admins?: number
  is_active?: boolean
  contact_person?: string
  contact_number?: string
  whatsapp_number?: string | null
  pin?: string
  upi_id?: string | null
  castes?: string[]
}

export interface TenantList {
  items: Tenant[]
  total: number
  page: number
  page_size: number
}

// ── API Error ────────────────────────────────────────────────────────────────
export interface ApiError {
  detail: string | { msg: string; type: string }[]
}
