<template>
  <v-app>
    <v-main class="bg-background">
      <v-container class="fill-height" fluid>
        <v-row align="center" justify="center" style="min-height: 100vh">
          <v-col cols="12" sm="8" md="6" lg="5">

            <!-- Loading state -->
            <div v-if="loading" class="text-center py-12">
              <v-progress-circular indeterminate color="primary" size="48" />
              <p class="text-body-2 text-medium-emphasis mt-4">Loading centre info…</p>
            </div>

            <!-- Not found -->
            <v-card v-else-if="notFound" elevation="4" rounded="xl" class="pa-8 text-center">
              <v-icon size="64" color="grey" class="mb-4">mdi-alert-circle-outline</v-icon>
              <h2 class="text-h6 font-weight-semibold mb-2">Centre Not Found</h2>
              <p class="text-body-2 text-medium-emphasis mb-6">
                The centre you're looking for doesn't exist or is no longer active.
              </p>
              <v-btn color="primary" variant="elevated" to="/login">Go to Login</v-btn>
            </v-card>

            <!-- Registration disabled -->
            <v-card v-else-if="tenantInfo && !tenantInfo.self_registration_enabled" elevation="4" rounded="xl" class="pa-8 text-center">
              <v-icon size="64" color="orange" class="mb-4">mdi-lock-outline</v-icon>
              <h2 class="text-h6 font-weight-semibold mb-2">Registration Closed</h2>
              <p class="text-body-2 text-medium-emphasis mb-2">
                Self-registration is currently disabled for <strong>{{ tenantInfo.name }}</strong>.
              </p>
              <p class="text-body-2 text-medium-emphasis mb-6">
                Please contact the centre administrator for an invite.
              </p>
              <v-btn color="primary" variant="elevated" to="/login">Go to Login</v-btn>
            </v-card>

            <!-- Registration success -->
            <v-card v-else-if="registered" elevation="4" rounded="xl" class="pa-8 text-center">
              <v-icon size="64" color="success" class="mb-4">mdi-check-circle</v-icon>
              <h2 class="text-h6 font-weight-semibold mb-2">Registration Successful!</h2>
              <p class="text-body-2 text-medium-emphasis mb-6">
                Your account has been created at <strong>{{ tenantInfo?.name }}</strong>.
                You can now log in with your email and password.
              </p>
              <v-btn color="primary" variant="elevated" size="large" to="/login" prepend-icon="mdi-login">
                Go to Login
              </v-btn>
            </v-card>

            <!-- Registration form -->
            <template v-else-if="tenantInfo">
              <!-- Branding -->
              <div class="text-center mb-6">
                <v-avatar v-if="tenantInfo.logo_key" size="72" rounded="lg" class="mb-3">
                  <v-img :src="logoUrl ?? undefined" />
                </v-avatar>
                <h1 class="text-h5 font-weight-bold text-primary">{{ tenantInfo.name }}</h1>
                <p class="text-body-2 text-medium-emphasis">Create your account to get started</p>
              </div>

              <v-card elevation="4" rounded="xl" class="pa-2">
                <v-card-text class="pa-6">
                  <h2 class="text-h6 font-weight-semibold mb-6 text-center">Register</h2>

                  <v-alert v-if="errorMsg" type="error" variant="tonal" rounded="lg" class="mb-4" closable @click:close="errorMsg = ''">
                    {{ errorMsg }}
                  </v-alert>

                  <v-form ref="formRef" v-model="valid" @submit.prevent="handleRegister">
                    <v-text-field
                      v-model="form.full_name"
                      label="Full Name"
                      prepend-inner-icon="mdi-account"
                      variant="outlined"
                      density="comfortable"
                      :rules="[rules.required, rules.minLen(2)]"
                      class="mb-3"
                      autocomplete="name"
                    />

                    <v-text-field
                      v-model="form.email"
                      label="Email Address"
                      type="email"
                      prepend-inner-icon="mdi-email-outline"
                      variant="outlined"
                      density="comfortable"
                      :rules="[rules.required, rules.email]"
                      class="mb-3"
                      autocomplete="email"
                    />

                    <!-- Phone + OTP block -->
                    <div class="mb-3">
                      <v-text-field
                        v-model="form.phone"
                        label="Mobile Number"
                        prepend-inner-icon="mdi-phone"
                        variant="outlined"
                        density="comfortable"
                        :rules="[rules.required, rules.phone]"
                        placeholder="+919876543210"
                        autocomplete="tel"
                        :disabled="requiresPhoneOtp && phoneVerified"
                        :append-inner-icon="requiresPhoneOtp && phoneVerified ? 'mdi-check-circle' : undefined"
                        :color="requiresPhoneOtp && phoneVerified ? 'success' : undefined"
                        hint="Include country code, e.g. +91 for India"
                        persistent-hint
                      />

                      <!-- OTP actions -->
                      <div v-if="requiresPhoneOtp && !phoneVerified" class="mt-2">
                        <div v-if="!otpSent">
                          <!-- reCAPTCHA container (invisible) -->
                          <div id="recaptcha-container" />
                          <v-btn
                            variant="tonal"
                            color="primary"
                            size="small"
                            :loading="sendingOtp"
                            :disabled="!isPhoneValid"
                            @click="sendOtp"
                          >
                            Send OTP
                          </v-btn>
                        </div>

                        <div v-else class="d-flex align-center gap-2 mt-1">
                          <v-text-field
                            v-model="otpCode"
                            label="Enter OTP"
                            prepend-inner-icon="mdi-numeric"
                            variant="outlined"
                            density="compact"
                            maxlength="6"
                            style="max-width: 180px"
                            :rules="[rules.required]"
                            hide-details
                          />
                          <v-btn
                            color="primary"
                            size="small"
                            :loading="verifyingOtp"
                            @click="verifyOtp"
                          >
                            Verify
                          </v-btn>
                          <v-btn
                            variant="text"
                            size="small"
                            color="grey"
                            @click="resetOtp"
                          >
                            Change
                          </v-btn>
                        </div>

                        <p v-if="otpError" class="text-caption text-error mt-1">{{ otpError }}</p>
                      </div>

                      <p v-else-if="requiresPhoneOtp" class="text-caption text-success mt-1">
                        <v-icon size="14" color="success">mdi-check</v-icon>
                        Mobile number verified
                      </p>

                      <p v-else class="text-caption text-medium-emphasis mt-1">
                        Phone OTP verification is disabled in this environment.
                      </p>
                    </div>

                    <v-select
                      v-model="form.gender"
                      label="Gender"
                      :items="[{ title: 'Male', value: 'male' }, { title: 'Female', value: 'female' }]"
                      prepend-inner-icon="mdi-gender-male-female"
                      variant="outlined"
                      density="comfortable"
                      :rules="[rules.required]"
                      class="mb-3"
                    />

                    <v-text-field
                      v-model="form.password"
                      label="Password"
                      :type="showPwd ? 'text' : 'password'"
                      prepend-inner-icon="mdi-lock-outline"
                      :append-inner-icon="showPwd ? 'mdi-eye-off' : 'mdi-eye'"
                      @click:append-inner="showPwd = !showPwd"
                      variant="outlined"
                      density="comfortable"
                      :rules="[rules.required, rules.password]"
                      class="mb-3"
                      hint="Min 8 chars, uppercase, lowercase, digit, special character"
                      persistent-hint
                      autocomplete="new-password"
                    />

                    <v-text-field
                      v-model="confirmPassword"
                      label="Confirm Password"
                      :type="showPwd ? 'text' : 'password'"
                      prepend-inner-icon="mdi-lock-check"
                      variant="outlined"
                      density="comfortable"
                      :rules="[rules.required, rules.match]"
                      class="mb-4"
                      autocomplete="new-password"
                    />

                    <v-btn
                      type="submit"
                      color="primary"
                      size="large"
                      block
                      :loading="submitting"
                      :disabled="!valid || (requiresPhoneOtp && !phoneVerified)"
                    >
                      Create Account
                    </v-btn>

                    <p v-if="requiresPhoneOtp && !phoneVerified" class="text-caption text-medium-emphasis text-center mt-2">
                      Please verify your mobile number before submitting
                    </p>
                  </v-form>

                  <div class="text-center mt-6">
                    <span class="text-body-2 text-medium-emphasis">Already have an account?</span>
                    <router-link to="/login" class="text-body-2 text-primary text-decoration-none ml-1">
                      Sign In
                    </router-link>
                  </div>
                </v-card-text>
              </v-card>
            </template>
          </v-col>
        </v-row>
      </v-container>
    </v-main>
  </v-app>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useHead } from '@unhead/vue'
import {
  RecaptchaVerifier,
  signInWithPhoneNumber,
  type ConfirmationResult,
} from 'firebase/auth'
import { getAuth } from 'firebase/auth'
import { firebaseApp } from '@/plugins/firebase'
import { publicApi } from '@/api/public'
import type { TenantPublicInfo } from '@/types'

const route = useRoute()
const slug = route.params.slug as string
const auth = getAuth(firebaseApp)

// ── Page state ───────────────────────────────────────────────────────────────
const loading = ref(true)
const notFound = ref(false)
const tenantInfo = ref<TenantPublicInfo | null>(null)
const logoUrl = ref<string | null>(null)

useHead(computed(() => ({
  title: tenantInfo.value ? `Join ${tenantInfo.value.name} — Varanbook` : 'Join — Varanbook',
  meta: [
    { name: 'description', content: tenantInfo.value ? `Register your matrimonial profile at ${tenantInfo.value.name}. Powered by Varanbook.` : 'Register your matrimonial profile. Powered by Varanbook.' },
    { name: 'robots', content: 'noindex, nofollow' },
  ],
})))
const registered = ref(false)
const submitting = ref(false)
const errorMsg = ref('')
const formRef = ref()
const valid = ref(false)
const showPwd = ref(false)
const confirmPassword = ref('')

// ── OTP state ────────────────────────────────────────────────────────────────
const otpSent = ref(false)
const sendingOtp = ref(false)
const verifyingOtp = ref(false)
const otpCode = ref('')
const otpError = ref('')
const phoneVerified = ref(false)
const firebaseIdToken = ref<string | null>(null)
let confirmationResult: ConfirmationResult | null = null
let recaptchaVerifier: RecaptchaVerifier | null = null

// ── Form data ────────────────────────────────────────────────────────────────
const form = ref({
  full_name: '',
  email: '',
  phone: '',
  gender: '' as 'male' | 'female' | '',
  password: '',
})

// ── Computed ─────────────────────────────────────────────────────────────────
const isPhoneValid = computed(() => /^\+[1-9]\d{6,14}$/.test(form.value.phone))
const requiresPhoneOtp = computed(() => tenantInfo.value?.phone_otp_enabled ?? false)

// ── Validation rules ─────────────────────────────────────────────────────────
const rules = {
  required: (v: string) => !!v || 'Required',
  minLen: (n: number) => (v: string) => v.length >= n || `Min ${n} characters`,
  email: (v: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v) || 'Invalid email',
  phone: (v: string) =>
    /^\+[1-9]\d{6,14}$/.test(v) || 'E.164 format required, e.g. +919876543210',
  password: (v: string) => {
    if (!v || v.length < 8) return 'Min 8 characters'
    if (!/[A-Z]/.test(v)) return 'Need at least one uppercase letter'
    if (!/[a-z]/.test(v)) return 'Need at least one lowercase letter'
    if (!/[0-9]/.test(v)) return 'Need at least one digit'
    if (!/[!@#$%^&*()\-_=+\[\]{}|;:,.<>?]/.test(v)) return 'Need at least one special character'
    return true
  },
  match: (v: string) => v === form.value.password || 'Passwords do not match',
}

function getOtpErrorMessage(err: any): string {
  const code = err?.code as string | undefined
  if (code === 'auth/billing-not-enabled') {
    return 'Phone OTP is not available for the current Firebase project. Enable billing for Firebase phone authentication or turn off FIREBASE_OTP_ENABLED on the backend for this environment.'
  }
  if (code === 'auth/invalid-phone-number') {
    return 'Invalid phone number. Use E.164 format, for example +919876543210.'
  }
  if (code === 'auth/too-many-requests') {
    return 'Too many OTP attempts. Wait a moment and try again.'
  }
  return err?.message ?? 'Failed to send OTP. Check the phone number and try again.'
}

// ── Load tenant info ─────────────────────────────────────────────────────────
onMounted(async () => {
  try {
    tenantInfo.value = await publicApi.getTenant(slug)
    if (tenantInfo.value.logo_key) {
      try {
        const { filesApi } = await import('@/api/profiles')
        const { url } = await filesApi.presignGet(tenantInfo.value.logo_key)
        logoUrl.value = url
      } catch {
        // Logo not accessible without auth — skip
      }
    }
  } catch {
    notFound.value = true
  } finally {
    loading.value = false
  }
})

// ── OTP: send ────────────────────────────────────────────────────────────────
async function sendOtp() {
  if (!isPhoneValid.value) return
  otpError.value = ''
  sendingOtp.value = true
  try {
    // Always clear any existing instance before creating a fresh one.
    // Reusing a verifier after signInWithPhoneNumber causes
    // "reCAPTCHA has already been rendered in this element".
    recaptchaVerifier?.clear()
    recaptchaVerifier = new RecaptchaVerifier(auth, 'recaptcha-container', {
      size: 'invisible',
    })
    confirmationResult = await signInWithPhoneNumber(
      auth,
      form.value.phone,
      recaptchaVerifier,
    )
    otpSent.value = true
  } catch (err: any) {
    otpError.value = getOtpErrorMessage(err)
    // Reset reCAPTCHA so it can be tried again
    recaptchaVerifier?.clear()
    recaptchaVerifier = null
  } finally {
    sendingOtp.value = false
  }
}

// ── OTP: verify ──────────────────────────────────────────────────────────────
async function verifyOtp() {
  if (!confirmationResult || !otpCode.value) return
  otpError.value = ''
  verifyingOtp.value = true
  try {
    const credential = await confirmationResult.confirm(otpCode.value)
    firebaseIdToken.value = await credential.user.getIdToken()
    phoneVerified.value = true
    otpSent.value = false
  } catch (err: any) {
    otpError.value = err?.message ?? 'Invalid OTP. Please try again.'
  } finally {
    verifyingOtp.value = false
  }
}

// ── OTP: reset (change number) ───────────────────────────────────────────────
function resetOtp() {
  otpSent.value = false
  otpCode.value = ''
  otpError.value = ''
  phoneVerified.value = false
  firebaseIdToken.value = null
  confirmationResult = null
  recaptchaVerifier?.clear()
  recaptchaVerifier = null
}

// ── Submit registration ───────────────────────────────────────────────────────
async function handleRegister() {
  const { valid: isValid } = await formRef.value.validate()
  if (!isValid || !phoneVerified.value) return

  submitting.value = true
  errorMsg.value = ''
  try {
    await publicApi.register(slug, {
      full_name: form.value.full_name,
      email: form.value.email,
      phone: form.value.phone,
      gender: form.value.gender as 'male' | 'female',
      password: form.value.password,
      phone_firebase_token: firebaseIdToken.value ?? undefined,
    })
    registered.value = true
  } catch (err: any) {
    const detail = err?.response?.data?.detail
    if (typeof detail === 'string') {
      errorMsg.value = detail
    } else if (Array.isArray(detail)) {
      errorMsg.value = detail.map((d: any) => d.msg).join(', ')
    } else {
      errorMsg.value = 'Registration failed. Please try again.'
    }
  } finally {
    submitting.value = false
  }
}
</script>
