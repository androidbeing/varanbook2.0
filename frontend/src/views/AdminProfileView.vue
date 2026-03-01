<template>
  <div>
    <!-- Header -->
    <v-row class="mb-6">
      <v-col>
        <v-card color="primary" rounded="xl" class="pa-6">
          <div class="d-flex align-center gap-4">
            <v-avatar color="white" size="64">
              <span class="text-h6 font-weight-bold text-primary">{{ initials }}</span>
            </v-avatar>
            <div>
              <h1 class="text-h5 font-weight-bold">My Account</h1>
              <p class="text-body-2 opacity-80 mb-0">
                {{ auth.user?.email }} &mdash;
                <v-chip size="x-small" color="white" variant="outlined" class="ml-1">Admin</v-chip>
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
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import client from '@/api/client'

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

// ── Profile form ──────────────────────────────────────────────────────────────
const profileForm = ref()
const profileValid = ref(false)
const savingProfile = ref(false)
const profileFields = ref({ full_name: '', phone: '' })

onMounted(() => {
  profileFields.value.full_name = auth.user?.full_name ?? ''
  profileFields.value.phone = (auth.user as any)?.phone ?? ''
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
