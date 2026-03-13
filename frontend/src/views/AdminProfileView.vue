<template>
  <div>
    <!-- Header -->
    <v-row class="mb-6">
      <v-col>
        <v-card color="primary" rounded="xl" class="pa-6">
          <div class="d-flex align-center ga-4">
            <!-- Clickable avatar with upload support -->
            <v-tooltip text="Click to change profile picture" location="bottom">
              <template #activator="{ props: tp }">
                <v-avatar
                  v-bind="tp"
                  color="white"
                  size="72"
                  class="cursor-pointer"
                  style="border: 3px solid rgba(255,255,255,0.6); overflow:hidden"
                  @click="avatarInput?.click()"
                >
                  <v-img v-if="avatarUrl" :src="avatarUrl" cover />
                  <span v-else class="text-h6 font-weight-bold text-primary">{{ initials }}</span>
                  <v-overlay
                    activator="parent"
                    class="d-flex align-center justify-center"
                    scrim="black"
                    :model-value="false"
                  >
                    <v-icon color="white" size="28">mdi-camera</v-icon>
                  </v-overlay>
                </v-avatar>
              </template>
            </v-tooltip>
            <input
              ref="avatarInput"
              type="file"
              accept="image/jpeg,image/png,image/webp"
              style="display:none"
              @change="uploadAvatar"
            />
            <div>
              <h1 class="text-h5 font-weight-bold">My Account</h1>
              <p class="text-body-2 opacity-80 mb-0">
                {{ auth.user?.email }} &mdash;
                <v-chip size="x-small" color="white" variant="outlined" class="ml-1">Admin</v-chip>
              </p>
              <p v-if="uploadingAvatar" class="text-caption opacity-70 mt-1 mb-0">
                <v-progress-circular indeterminate size="12" width="2" color="white" class="mr-1" />
                Uploading…
              </p>
            </div>
          </div>
        </v-card>
      </v-col>
    </v-row>

    <v-row>
      <!-- ── Account Details ──────────────────────────────────────────────── -->
      <v-col cols="12" md="6">
        <v-card rounded="xl" class="mb-4">
          <v-card-title class="pa-5 pb-2 text-subtitle-1 font-weight-semibold">
            <v-icon class="mr-2" size="20">mdi-account-edit</v-icon>Account Details
          </v-card-title>
          <v-card-text class="pa-5 pt-2">
            <v-form ref="profileForm" v-model="profileValid" @submit.prevent="saveProfile">
              <v-text-field
                v-model="profileFields.full_name"
                label="Full Name"
                variant="outlined"
                density="compact"
                class="mb-3"
                :rules="[required, minLen(2)]"
                prepend-inner-icon="mdi-account"
              />
              <v-text-field
                :model-value="auth.user?.email"
                label="Email"
                variant="outlined"
                density="compact"
                class="mb-3"
                readonly
                prepend-inner-icon="mdi-email"
                hint="Email cannot be changed"
                persistent-hint
              />
              <v-text-field
                v-model="profileFields.phone"
                label="Phone (optional)"
                variant="outlined"
                density="compact"
                class="mb-4"
                :rules="[optionalPhone]"
                prepend-inner-icon="mdi-phone"
                placeholder="+919876543210"
              />
              <v-btn
                type="submit"
                color="primary"
                variant="elevated"
                :loading="savingProfile"
                :disabled="!profileValid"
                block
              >
                Save Changes
              </v-btn>
            </v-form>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- ── Change Password ──────────────────────────────────────────────── -->
      <v-col cols="12" md="6">
        <v-card rounded="xl" class="mb-4">
          <v-card-title class="pa-5 pb-2 text-subtitle-1 font-weight-semibold">
            <v-icon class="mr-2" size="20">mdi-lock-reset</v-icon>Change Password
          </v-card-title>
          <v-card-text class="pa-5 pt-2">
            <v-form ref="pwdForm" v-model="pwdValid" @submit.prevent="changePassword">
              <v-text-field
                v-model="pwdFields.current_password"
                label="Current Password"
                variant="outlined"
                density="compact"
                class="mb-3"
                :type="showCurrent ? 'text' : 'password'"
                :append-inner-icon="showCurrent ? 'mdi-eye-off' : 'mdi-eye'"
                @click:append-inner="showCurrent = !showCurrent"
                :rules="[required]"
                prepend-inner-icon="mdi-lock"
              />
              <v-text-field
                v-model="pwdFields.new_password"
                label="New Password"
                variant="outlined"
                density="compact"
                class="mb-3"
                :type="showNew ? 'text' : 'password'"
                :append-inner-icon="showNew ? 'mdi-eye-off' : 'mdi-eye'"
                @click:append-inner="showNew = !showNew"
                :rules="[required, passwordRule]"
                prepend-inner-icon="mdi-lock-plus"
                hint="Min 8 chars, uppercase, lowercase, digit, special char"
                persistent-hint
              />
              <v-text-field
                v-model="confirmPassword"
                label="Confirm New Password"
                variant="outlined"
                density="compact"
                class="mb-4"
                :type="showNew ? 'text' : 'password'"
                :rules="[required, matchRule]"
                prepend-inner-icon="mdi-lock-check"
              />
              <v-btn
                type="submit"
                color="warning"
                variant="elevated"
                :loading="savingPwd"
                :disabled="!pwdValid"
                block
              >
                Update Password
              </v-btn>
            </v-form>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- ── Read-only Info ───────────────────────────────────────────────── -->
      <v-col cols="12">
        <v-card rounded="xl" class="mb-4">
          <v-card-title class="pa-5 pb-2 text-subtitle-1 font-weight-semibold">
            <v-icon class="mr-2" size="20">mdi-storefront-outline</v-icon>Tenant / Centre Logo
          </v-card-title>
          <v-card-text class="pa-5 pt-2">
            <div class="d-flex align-center ga-4 flex-wrap">
              <v-avatar size="80" rounded="lg" color="grey-lighten-3" style="border:2px dashed #bbb">
                <v-img v-if="logoUrl" :src="logoUrl" cover />
                <v-icon v-else size="36" color="grey-darken-1">mdi-image-outline</v-icon>
              </v-avatar>
              <div>
                <p class="text-body-2 mb-2 text-medium-emphasis">
                  Upload your matrimonial centre's logo.<br />
                  Supported: JPG, PNG, WebP · Max recommended: 512 KB
                </p>
                <v-btn
                  color="primary"
                  variant="tonal"
                  prepend-icon="mdi-upload"
                  :loading="uploadingLogo"
                  @click="logoInput?.click()"
                >
                  {{ logoUrl ? 'Replace Logo' : 'Upload Logo' }}
                </v-btn>
                <input
                  ref="logoInput"
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  style="display:none"
                  @change="uploadLogo"
                />
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- ── Payment Information ──────────────────────────────────────────── -->
      <v-col cols="12">
        <v-card rounded="xl" class="mb-4">
          <v-card-title class="pa-5 pb-2 text-subtitle-1 font-weight-semibold">
            <v-icon class="mr-2" size="20">mdi-cash-fast</v-icon>Payment Information
          </v-card-title>
          <v-card-text class="pa-5 pt-0">
            <p class="text-body-2 text-medium-emphasis mb-4">
              These details will be shown to members on their Membership screen so they can make payments.
            </p>
            <v-form ref="paymentForm" v-model="paymentValid" @submit.prevent="savePaymentInfo">
              <v-row>
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="paymentFields.upi_name"
                    label="UPI Account Name"
                    variant="outlined"
                    density="compact"
                    class="mb-3"
                    prepend-inner-icon="mdi-account-cash"
                    placeholder="e.g. Sharma Vivah Kendra"
                    hint="Name displayed on UPI for verification"
                    persistent-hint
                  />
                </v-col>
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="paymentFields.upi_id"
                    label="UPI ID"
                    variant="outlined"
                    density="compact"
                    class="mb-3"
                    prepend-inner-icon="mdi-at"
                    placeholder="e.g. vivahkendra@upi"
                    :rules="[optionalUpi]"
                    hint="Your UPI address for receiving payments"
                    persistent-hint
                  />
                </v-col>
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="paymentFields.payment_whatsapp"
                    label="WhatsApp Number (for payment confirmation)"
                    variant="outlined"
                    density="compact"
                    class="mb-3"
                    prepend-inner-icon="mdi-whatsapp"
                    placeholder="+919876543210"
                    :rules="[optionalPhone]"
                    hint="Members will send payment screenshots to this number"
                    persistent-hint
                  />
                </v-col>
                <v-col cols="12" sm="6">
                  <div class="d-flex align-center ga-4 flex-wrap">
                    <v-avatar size="80" rounded="lg" color="grey-lighten-3" style="border:2px dashed #bbb">
                      <v-img v-if="upiQrUrl" :src="upiQrUrl" cover />
                      <v-icon v-else size="36" color="grey-darken-1">mdi-qrcode</v-icon>
                    </v-avatar>
                    <div>
                      <p class="text-body-2 mb-2 text-medium-emphasis">
                        Upload your UPI QR code image.<br />
                        Supported: JPG, PNG, WebP
                      </p>
                      <v-btn
                        color="primary"
                        variant="tonal"
                        prepend-icon="mdi-qrcode-scan"
                        :loading="uploadingQr"
                        @click="qrInput?.click()"
                        size="small"
                      >
                        {{ upiQrUrl ? 'Replace QR Code' : 'Upload QR Code' }}
                      </v-btn>
                      <input
                        ref="qrInput"
                        type="file"
                        accept="image/jpeg,image/png,image/webp"
                        style="display:none"
                        @change="uploadUpiQr"
                      />
                    </div>
                  </div>
                </v-col>
              </v-row>
              <v-btn
                type="submit"
                color="primary"
                variant="elevated"
                :loading="savingPayment"
                :disabled="!paymentValid"
                class="mt-2"
                block
              >
                Save Payment Details
              </v-btn>
            </v-form>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- ── Read-only Info ───────────────────────────────────────────────── -->
      <v-col cols="12">
        <v-card rounded="xl">
          <v-card-title class="pa-5 pb-2 text-subtitle-1 font-weight-semibold">
            <v-icon class="mr-2" size="20">mdi-information-outline</v-icon>Account Info
          </v-card-title>
          <v-card-text class="pa-5 pt-2">
            <v-row dense>
              <v-col cols="12" sm="6" md="3">
                <div class="text-caption text-medium-emphasis mb-1">Role</div>
                <v-chip color="blue" variant="tonal" size="small">Admin</v-chip>
              </v-col>
              <v-col cols="12" sm="6" md="3">
                <div class="text-caption text-medium-emphasis mb-1">Tenant ID</div>
                <div class="text-body-2 font-weight-medium">{{ auth.user?.tenant_id ?? '—' }}</div>
              </v-col>
              <v-col cols="12" sm="6" md="3">
                <div class="text-caption text-medium-emphasis mb-1">Account Status</div>
                <v-chip :color="auth.user?.is_active ? 'success' : 'error'" size="small">
                  {{ auth.user?.is_active ? 'Active' : 'Inactive' }}
                </v-chip>
              </v-col>
              <v-col cols="12" sm="6" md="3">
                <div class="text-caption text-medium-emphasis mb-1">Member Since</div>
                <div class="text-body-2">{{ formatDate(auth.user?.created_at) }}</div>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Snackbar -->
    <v-snackbar v-model="snack.show" :color="snack.color" timeout="3000" location="top right">
      {{ snack.message }}
    </v-snackbar>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import client from '@/api/client'
import { filesApi } from '@/api/profiles'
import { membershipApi } from '@/api/membership_plans'

const auth = useAuthStore()

// ── Initials ──────────────────────────────────────────────────────────────────
const initials = computed(() =>
  (auth.user?.full_name ?? '')
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2),
)

// ── Avatar / logo state ───────────────────────────────────────────────────────
const avatarInput = ref<HTMLInputElement | null>(null)
const logoInput = ref<HTMLInputElement | null>(null)
const avatarUrl = ref<string | null>(null)
const logoUrl = ref<string | null>(null)
const uploadingAvatar = ref(false)
const uploadingLogo = ref(false)

async function resolvePresignedUrl(key: string | null | undefined): Promise<string | null> {
  if (!key) return null
  try {
    const { url } = await filesApi.presignGet(key)
    return url
  } catch {
    return null
  }
}

async function refreshAvatarUrl() {
  avatarUrl.value = await resolvePresignedUrl(auth.user?.avatar_key)
}

// Tenant logo key is stored on the tenant, not on the user.
// We need the tenant info – expose via /admin/tenants/me or store locally.
// For now we'll store the key client-side after a successful upload.
const _tenantLogoKey = ref<string | null>(null)

async function uploadAvatar(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  uploadingAvatar.value = true
  try {
    // 1. Get presigned PUT URL
    const { upload_url, object_key } = await filesApi.presignAvatar({
      file_name: file.name,
      content_type: file.type,
      purpose: 'avatar',
    })
    // 2. PUT directly to S3
    await filesApi.putToS3(upload_url, file)
    // 3. Register on user
    await filesApi.registerAvatar(object_key)
    // 4. Refresh local auth user and avatar URL
    await auth.fetchMe()
    avatarUrl.value = await resolvePresignedUrl(object_key)
    showSnack('Profile picture updated!')
  } catch (err: any) {
    const detail = err?.response?.data?.detail ?? err?.message ?? 'Avatar upload failed'
    showSnack(typeof detail === 'string' ? detail : 'Avatar upload failed. Check S3 config.', 'error')
  } finally {
    uploadingAvatar.value = false
    // Reset the input so the same file can be re-selected
    if (avatarInput.value) avatarInput.value.value = ''
  }
}

async function uploadLogo(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  uploadingLogo.value = true
  try {
    const { upload_url, object_key } = await filesApi.presignAvatar({
      file_name: file.name,
      content_type: file.type,
      purpose: 'tenant_logo',
    })
    await filesApi.putToS3(upload_url, file)
    await filesApi.registerTenantLogo(object_key)
    _tenantLogoKey.value = object_key
    logoUrl.value = await resolvePresignedUrl(object_key)
    showSnack('Tenant logo updated!')
  } catch (err: any) {
    // axios error (backend) → err.response.data.detail
    // fetch/network error (S3 PUT) → err.message
    const detail = err?.response?.data?.detail ?? err?.message ?? 'Logo upload failed'
    showSnack(typeof detail === 'string' ? detail : 'Logo upload failed. Check S3 config.', 'error')
  } finally {
    uploadingLogo.value = false
    if (logoInput.value) logoInput.value.value = ''
  }
}

// ── Profile form ──────────────────────────────────────────────────────────────
const profileForm = ref()
const profileValid = ref(false)
const savingProfile = ref(false)
const profileFields = ref({ full_name: '', phone: '' })

// ── Payment Info ──────────────────────────────────────────────────────────────
const paymentForm = ref()
const paymentValid = ref(true)
const savingPayment = ref(false)
const qrInput = ref<HTMLInputElement | null>(null)
const upiQrUrl = ref<string | null>(null)
const uploadingQr = ref(false)
const paymentFields = ref({ upi_name: '', upi_id: '', payment_whatsapp: '' })

async function loadPaymentInfo() {
  try {
    const info = await membershipApi.getPaymentInfo()
    paymentFields.value.upi_name = info.upi_name ?? ''
    paymentFields.value.upi_id = info.upi_id ?? ''
    paymentFields.value.payment_whatsapp = info.payment_whatsapp ?? ''
    upiQrUrl.value = await resolvePresignedUrl(info.upi_qr_key)
  } catch {
    // Payment info may not exist yet
  }
}

async function savePaymentInfo() {
  savingPayment.value = true
  try {
    await membershipApi.updatePaymentInfo({
      upi_name: paymentFields.value.upi_name || null,
      upi_id: paymentFields.value.upi_id || null,
      payment_whatsapp: paymentFields.value.payment_whatsapp || null,
    })
    showSnack('Payment details saved successfully!')
  } catch (e: any) {
    const detail = e?.response?.data?.detail
    showSnack(typeof detail === 'string' ? detail : 'Failed to save payment details', 'error')
  } finally {
    savingPayment.value = false
  }
}

async function uploadUpiQr(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  uploadingQr.value = true
  try {
    const { upload_url, object_key } = await filesApi.presignAvatar({
      file_name: file.name,
      content_type: file.type,
      purpose: 'upi_qr',
    })
    await filesApi.putToS3(upload_url, file)
    await filesApi.registerTenantUpiQr(object_key)
    upiQrUrl.value = await resolvePresignedUrl(object_key)
    showSnack('UPI QR code uploaded!')
  } catch (err: any) {
    const detail = err?.response?.data?.detail ?? err?.message ?? 'QR upload failed'
    showSnack(typeof detail === 'string' ? detail : 'QR upload failed.', 'error')
  } finally {
    uploadingQr.value = false
    if (qrInput.value) qrInput.value.value = ''
  }
}

onMounted(() => {
  profileFields.value.full_name = auth.user?.full_name ?? ''
  profileFields.value.phone = (auth.user as any)?.phone ?? ''
  refreshAvatarUrl()
  loadPaymentInfo()
})

// ── Password form ─────────────────────────────────────────────────────────────
const pwdForm = ref()
const pwdValid = ref(false)
const savingPwd = ref(false)
const showCurrent = ref(false)
const showNew = ref(false)
const pwdFields = ref({ current_password: '', new_password: '' })
const confirmPassword = ref('')

// ── Snack ─────────────────────────────────────────────────────────────────────
const snack = ref({ show: false, message: '', color: 'success' })
function showSnack(msg: string, color = 'success') {
  snack.value = { show: true, message: msg, color }
}

// ── Validation ────────────────────────────────────────────────────────────────
const required = (v: string) => !!v || 'Required'
const minLen = (n: number) => (v: string) => v.length >= n || `Min ${n} characters`
const optionalPhone = (v: string) =>
  !v || /^\+[1-9]\d{6,14}$/.test(v) || 'E.164 format required, e.g. +919876543210'
const optionalUpi = (v: string) =>
  !v || /^[\w.\-]+@[\w.\-]+$/.test(v) || 'Invalid UPI ID format, e.g. name@upi'
const passwordRule = (v: string) => {
  if (!v || v.length < 8) return 'Min 8 characters'
  if (!/[A-Z]/.test(v)) return 'Need at least one uppercase letter'
  if (!/[a-z]/.test(v)) return 'Need at least one lowercase letter'
  if (!/[0-9]/.test(v)) return 'Need at least one digit'
  if (!/[!@#$%^&*()\-_=+\[\]{}|;:,.<>?]/.test(v)) return 'Need at least one special character'
  return true
}
const matchRule = (v: string) => v === pwdFields.value.new_password || 'Passwords do not match'

// ── Helpers ───────────────────────────────────────────────────────────────────
function formatDate(dt?: string) {
  if (!dt) return '—'
  return new Date(dt).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
}

// ── Actions ───────────────────────────────────────────────────────────────────
async function saveProfile() {
  const { valid } = await profileForm.value.validate()
  if (!valid) return
  savingProfile.value = true
  try {
    const updated = await client.patch('/users/me', {
      full_name: profileFields.value.full_name,
      phone: profileFields.value.phone || null,
    }).then((r) => r.data)
    // Refresh auth store user
    await auth.fetchMe()
    showSnack('Profile updated successfully')
  } catch (e: any) {
    const detail = e?.response?.data?.detail
    showSnack(typeof detail === 'string' ? detail : 'Failed to update profile', 'error')
  } finally {
    savingProfile.value = false
  }
}

async function changePassword() {
  const { valid } = await pwdForm.value.validate()
  if (!valid) return
  savingPwd.value = true
  try {
    await client.post('/auth/change-password', {
      current_password: pwdFields.value.current_password,
      new_password: pwdFields.value.new_password,
    })
    showSnack('Password changed successfully')
    pwdFields.value = { current_password: '', new_password: '' }
    confirmPassword.value = ''
    pwdForm.value.reset()
  } catch (e: any) {
    const detail = e?.response?.data?.detail
    showSnack(typeof detail === 'string' ? detail : 'Failed to change password', 'error')
  } finally {
    savingPwd.value = false
  }
}
</script>
