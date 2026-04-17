<template>
  <v-app>
    <v-main class="bg-background">
      <v-container class="fill-height" fluid>
        <v-row align="center" justify="center" style="min-height: 100vh">
          <v-col cols="12" sm="8" md="5" lg="4">
            <div class="text-center mb-8">
              <h1 class="text-h4 font-weight-bold text-primary mt-2">Varanbook</h1>
              <p class="text-body-2 text-medium-emphasis">Find your perfect match</p>
            </div>

            <v-card elevation="4" rounded="xl" class="pa-2">
              <v-card-text class="pa-6">
                <h2 class="text-h6 font-weight-semibold mb-4 text-center">Forgot Password</h2>

                <!-- Method tabs -->
                <v-tabs v-model="method" color="primary" class="mb-5" grow>
                  <v-tab value="email">
                    <v-icon start>mdi-email-outline</v-icon>
                    By Email
                  </v-tab>
                  <v-tab value="phone">
                    <v-icon start>mdi-phone</v-icon>
                    By Phone OTP
                  </v-tab>
                </v-tabs>

                <!-- ── Email tab ── -->
                <div v-if="method === 'email'">
                  <p class="text-body-2 text-medium-emphasis text-center mb-5">
                    Enter the email address linked to your account and we'll send you a reset link.
                  </p>
                  <v-form ref="emailFormRef" v-model="emailValid" @submit.prevent="handleEmailSubmit">
                    <v-text-field
                      v-model="email"
                      label="Email address"
                      type="email"
                      prepend-inner-icon="mdi-email-outline"
                      variant="outlined"
                      density="comfortable"
                      :rules="[rules.required, rules.email]"
                      class="mb-4"
                      autocomplete="email"
                    />
                    <v-btn
                      type="submit"
                      color="primary"
                      size="large"
                      block
                      :loading="emailLoading"
                      :disabled="!emailValid"
                    >
                      Send Reset Link
                    </v-btn>
                  </v-form>
                </div>

                <!-- ── Phone OTP tab ── -->
                <div v-else>
                  <p class="text-body-2 text-medium-emphasis text-center mb-5">
                    Verify your mobile number with an OTP and we'll let you reset your password immediately.
                  </p>

                  <v-alert v-if="phoneError" type="error" variant="tonal" rounded="lg" class="mb-4" closable @click:close="phoneError = ''">
                    {{ phoneError }}
                  </v-alert>

                  <!-- Step 1: enter phone -->
                  <div v-if="!phoneVerified">
                    <v-text-field
                      v-model="phone"
                      label="Mobile Number"
                      prepend-inner-icon="mdi-phone"
                      variant="outlined"
                      density="comfortable"
                      :rules="[rules.required, rules.phone]"
                      placeholder="+919876543210"
                      autocomplete="tel"
                      :disabled="otpSent"
                      hint="Include country code, e.g. +91 for India"
                      persistent-hint
                      class="mb-3"
                    />

                    <div v-if="!otpSent">
                      <div id="fp-recaptcha-container" />
                      <v-btn
                        color="primary"
                        size="large"
                        block
                        :loading="sendingOtp"
                        :disabled="!isPhoneValid"
                        @click="sendOtp"
                      >
                        Send OTP
                      </v-btn>
                    </div>

                    <div v-else>
                      <v-text-field
                        v-model="otpCode"
                        label="Enter OTP"
                        prepend-inner-icon="mdi-numeric"
                        variant="outlined"
                        density="comfortable"
                        maxlength="6"
                        class="mb-3"
                      />
                      <v-btn
                        color="primary"
                        size="large"
                        block
                        :loading="verifyingOtp"
                        :disabled="otpCode.length < 4"
                        @click="verifyOtp"
                        class="mb-2"
                      >
                        Verify OTP
                      </v-btn>
                      <v-btn variant="text" size="small" color="grey" block @click="resetOtp">
                        Change Number
                      </v-btn>
                    </div>
                  </div>

                  <!-- Step 2: phone verified, show success prompt -->
                  <div v-else class="text-center">
                    <v-icon size="48" color="success" class="mb-3">mdi-check-circle</v-icon>
                    <p class="text-body-2 mb-1">Phone verified successfully.</p>
                    <p class="text-caption text-medium-emphasis">Redirecting to reset password…</p>
                    <v-progress-linear indeterminate color="primary" class="mt-3" />
                  </div>
                </div>

                <div class="text-center mt-5">
                  <router-link to="/login" class="text-caption text-primary text-decoration-none">
                    Back to Login
                  </router-link>
                </div>
              </v-card-text>
            </v-card>

            <p class="text-center text-caption text-medium-emphasis mt-6">
              © {{ new Date().getFullYear() }} Varanbook. All rights reserved.
            </p>
          </v-col>
        </v-row>
      </v-container>
    </v-main>

    <!-- Email success dialog -->
    <v-dialog v-model="successDialog" max-width="380" persistent>
      <v-card rounded="xl">
        <v-card-title class="text-h6 pt-5 px-6">Check your inbox</v-card-title>
        <v-card-text class="px-6 pb-4">
          If that email is registered, a password reset link has been sent. Please check your inbox (and spam folder).
        </v-card-text>
        <v-card-actions class="px-6 pb-5 justify-end">
          <v-btn color="primary" variant="flat" min-width="80" @click="goToLogin">OK</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Email error dialog -->
    <v-dialog v-model="errorDialog" max-width="360" persistent>
      <v-card rounded="xl">
        <v-card-title class="text-h6 pt-5 px-6">Something went wrong</v-card-title>
        <v-card-text class="px-6 pb-4">Unable to process your request. Please try again later.</v-card-text>
        <v-card-actions class="px-6 pb-5 justify-end">
          <v-btn color="primary" variant="flat" min-width="80" @click="errorDialog = false">OK</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-app>
</template>

<script lang="ts" setup>
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  RecaptchaVerifier,
  signInWithPhoneNumber,
  getAuth,
  type ConfirmationResult,
} from 'firebase/auth'
import { firebaseApp } from '@/plugins/firebase'
import { authApi } from '@/api/auth'

const router = useRouter()
const auth = getAuth(firebaseApp)

// ── Shared ───────────────────────────────────────────────────────────────────
const method = ref<'email' | 'phone'>('email')

// Clean up reCAPTCHA when leaving the phone tab so the verifier isn't stale
// when the user switches back and the container div is remounted.
watch(method, (tab) => {
  if (tab !== 'phone') {
    recaptchaVerifier?.clear()
    recaptchaVerifier = null
    confirmationResult = null
    otpSent.value = false
  }
})

const rules = {
  required: (v: string) => !!v || 'Required',
  email: (v: string) => /.+@.+\..+/.test(v) || 'Enter a valid email',
  phone: (v: string) =>
    /^\+[1-9]\d{6,14}$/.test(v) || 'E.164 format required, e.g. +919876543210',
}

// ── Email tab ────────────────────────────────────────────────────────────────
const emailFormRef = ref()
const emailValid = ref(false)
const email = ref('')
const emailLoading = ref(false)
const successDialog = ref(false)
const errorDialog = ref(false)

async function handleEmailSubmit() {
  const { valid: ok } = await emailFormRef.value.validate()
  if (!ok) return
  emailLoading.value = true
  try {
    await authApi.requestPasswordReset(email.value)
    successDialog.value = true
  } catch {
    errorDialog.value = true
  } finally {
    emailLoading.value = false
  }
}

function goToLogin() {
  successDialog.value = false
  router.push('/login')
}

// ── Phone OTP tab ─────────────────────────────────────────────────────────────
const phone = ref('')
const otpSent = ref(false)
const sendingOtp = ref(false)
const verifyingOtp = ref(false)
const otpCode = ref('')
const phoneError = ref('')
const phoneVerified = ref(false)
let confirmationResult: ConfirmationResult | null = null
let recaptchaVerifier: RecaptchaVerifier | null = null

const isPhoneValid = computed(() => /^\+[1-9]\d{6,14}$/.test(phone.value))

async function sendOtp() {
  if (!isPhoneValid.value) return
  phoneError.value = ''
  sendingOtp.value = true
  try {
    // Always clear any existing instance before creating a fresh one.
    // Reusing a verifier after signInWithPhoneNumber causes
    // "reCAPTCHA has already been rendered in this element".
    recaptchaVerifier?.clear()
    recaptchaVerifier = new RecaptchaVerifier(auth, 'fp-recaptcha-container', {
      size: 'invisible',
    })
    confirmationResult = await signInWithPhoneNumber(auth, phone.value, recaptchaVerifier)
    otpSent.value = true
  } catch (err: any) {
    phoneError.value = err?.message ?? 'Failed to send OTP. Check the number and try again.'
    recaptchaVerifier?.clear()
    recaptchaVerifier = null
  } finally {
    sendingOtp.value = false
  }
}

async function verifyOtp() {
  if (!confirmationResult || !otpCode.value) return
  phoneError.value = ''
  verifyingOtp.value = true
  try {
    const credential = await confirmationResult.confirm(otpCode.value)
    const idToken = await credential.user.getIdToken()

    // Call backend: verify token + get reset token
    const { reset_token } = await authApi.forgotPasswordByPhone(phone.value, idToken)
    phoneVerified.value = true

    // Short delay so the user sees the success state, then redirect
    setTimeout(() => {
      router.push(`/reset-password?token=${encodeURIComponent(reset_token)}`)
    }, 1500)
  } catch (err: any) {
    const detail = err?.response?.data?.detail
    if (typeof detail === 'string') {
      phoneError.value = detail
    } else {
      phoneError.value = err?.message ?? 'OTP verification failed. Please try again.'
    }
  } finally {
    verifyingOtp.value = false
  }
}

function resetOtp() {
  otpSent.value = false
  otpCode.value = ''
  phoneError.value = ''
  confirmationResult = null
  recaptchaVerifier?.clear()
  recaptchaVerifier = null
}
</script>
