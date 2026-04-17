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
  phone?: string | null
  role: UserRole
  is_active: boolean
  tenant_id: string | null
  /** S3 object key for the user's profile picture. Resolve to a URL via /files/presign-get */
  avatar_key?: string | null
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
  // "accepted" when viewer has a mutually confirmed shortlist connection with this profile
  connection_status?: string | null
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

// ── Membership Plans ─────────────────────────────────────────────────────────
export interface TenantPlan {
  id: string
  name: string
  tagline: string | null
  duration_months: number
  base_price_inr: number
  effective_price_inr: number
  has_override: boolean
  description: string | null
  features: string[] | null
  is_active: boolean
  sort_order: number
}

export type SubscriptionStatus = 'active' | 'expired' | 'cancelled'

export interface Subscription {
  id: string
  user_id: string
  tenant_id: string
  plan_template_id: string
  plan_name: string
  plan_tagline: string | null
  duration_months: number
  price_paid_inr: number
  starts_at: string
  expires_at: string
  status: SubscriptionStatus
  notes: string | null
  created_by_id: string | null
  created_at: string
  updated_at: string
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
  upi_name: string | null
  upi_qr_key: string | null
  payment_whatsapp: string | null
  castes: string[] | null
  self_registration_enabled: boolean
  active_members_count: number
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
  upi_name?: string | null
  payment_whatsapp?: string | null
  castes?: string[]
}

export interface TenantList {
  items: Tenant[]
  total: number
  page: number
  page_size: number
}

// ── Tenant Payment Info ──────────────────────────────────────────────────────
export interface TenantPaymentInfo {
  upi_id: string | null
  upi_name: string | null
  upi_qr_key: string | null
  payment_whatsapp: string | null
  tenant_name: string | null
}

// ── API Error ────────────────────────────────────────────────────────────────
// ── Public / Self-Registration ──────────────────────────────────────────────────
export interface TenantPublicInfo {
  name: string
  slug: string
  logo_key: string | null
  self_registration_enabled: boolean
  phone_otp_enabled: boolean
}

export interface SelfRegisterPayload {
  full_name: string
  email: string
  /** E.164 phone number — required for OTP verification */
  phone: string
  gender: 'male' | 'female'
  password: string
  /** Firebase ID token from phone OTP confirmation — sent to backend for verification */
  phone_firebase_token?: string
}

export interface SelfRegistrationStatus {
  enabled: boolean
  join_url_slug: string | null
}

// ── API Error ──────────────────────────────────────────────────────────────────export interface ApiError {
  detail: string | { msg: string; type: string }[]
}

// ── Shortlist ────────────────────────────────────────────────────────────────
export type ShortlistStatus = 'shortlisted' | 'accepted' | 'rejected'

export interface ShortlistEntry {
  id: string
  tenant_id: string
  from_profile_id: string
  to_profile_id: string
  status: ShortlistStatus
  note: string | null
  created_at: string
  updated_at: string
}

export interface ShortlistList {
  items: ShortlistEntry[]
  total: number
}

export interface InterestEntry {
  shortlist_id: string
  status: ShortlistStatus
  note: string | null
  created_at: string
  profile: Profile
}

export interface InterestList {
  items: InterestEntry[]
  total: number
  page: number
  size: number
  pages: number
}
