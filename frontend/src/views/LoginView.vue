<template>
  <v-app>
    <v-main class="bg-background">
      <v-container class="fill-height" fluid>
        <v-row align="center" justify="center" style="min-height: 100vh">
          <v-col cols="12" sm="8" md="5" lg="4">
            <!-- Branding -->
            <div class="text-center mb-8">
              <router-link to="/" class="text-decoration-none">
                <h1 class="text-h4 font-weight-bold text-primary mt-2">Varanbook</h1>
              </router-link>
              <p class="text-body-2 text-medium-emphasis">Find your perfect match</p>
            </div>

            <v-card elevation="4" rounded="xl" class="pa-2">
              <v-card-text class="pa-6">
                <h2 class="text-h6 font-weight-semibold mb-4 text-center">Sign In</h2>

                <!-- Tab switcher -->
                <v-tabs v-model="tab" grow color="primary" class="mb-5" density="compact">
                  <v-tab value="email">
                    <v-icon start size="16">mdi-email-outline</v-icon>
                    Email
                  </v-tab>
                  <v-tab value="otp">
                    <v-icon start size="16">mdi-cellphone-key</v-icon>
                    Phone OTP
                  </v-tab>
                </v-tabs>

                <!-- ── Email / Password tab ─────────────────────────── -->
                <v-tabs-window v-model="tab">
                  <v-tabs-window-item value="email">
                    <v-form ref="emailFormRef" v-model="emailValid" @submit.prevent="handleEmailLogin">
                      <v-text-field
                        v-model="email"
                        label="Email address"
                        type="email"
                        prepend-inner-icon="mdi-email-outline"
                        variant="outlined"
                        density="comfortable"
                        :rules="[rules.required, rules.email]"
                        class="mb-3"
                        autocomplete="email"
                      />

                      <v-text-field
                        v-model="password"
                        label="Password"
                        :type="showPwd ? 'text' : 'password'"
                        prepend-inner-icon="mdi-lock-outline"
                        :append-inner-icon="showPwd ? 'mdi-eye-off' : 'mdi-eye'"
                        @click:append-inner="showPwd = !showPwd"
                        variant="outlined"
                        density="comfortable"
                        :rules="[rules.required]"
                        class="mb-2"
                        autocomplete="current-password"
                      />

                      <div class="text-right mb-4">
                        <router-link
                          to="/forgot-password"
                          class="text-caption text-primary text-decoration-none"
                        >Forgot password?</router-link>
                      </div>

                      <v-btn
                        type="submit"
                        color="primary"
                        size="large"
                        block
                        :loading="auth.loading"
                        :disabled="!emailValid"
                      >
                        Sign In
                      </v-btn>
                    </v-form>
                  </v-tabs-window-item>

                  <!-- ── Phone OTP tab ──────────────────────────────── -->
                  <v-tabs-window-item value="otp">
                    <!-- Step 1: enter phone -->
                    <div v-if="!otpSent">
                      <v-text-field
                        v-model="phone"
                        label="Mobile number"
                        placeholder="+919876543210"
                        prepend-inner-icon="mdi-phone-outline"
                        variant="outlined"
                        density="comfortable"
                        hint="Include country code, e.g. +91"
                        persistent-hint
                        class="mb-4"
                        :error-messages="phoneError"
                      />
                      <div id="recaptcha-container" class="mb-3" />
                      <v-btn
                        color="primary"
                        size="large"
                        block
                        :loading="sendingOtp"
                        :disabled="!isPhoneValid"
                        @click="sendOtp"
                      >
                        <v-icon start>mdi-message-arrow-right-outline</v-icon>
                        Send OTP
                      </v-btn>
                    </div>

                    <!-- Step 2: enter OTP code -->
                    <div v-else>
                      <p class="text-body-2 text-medium-emphasis mb-4 text-center">
                        OTP sent to <strong>{{ phone }}</strong>
                        <v-btn variant="text" size="x-small" color="primary" class="ml-1" @click="resetOtp">Change</v-btn>
                      </p>

                      <v-otp-input
                        v-model="otpCode"
                        length="6"
                        type="number"
                        variant="outlined"
                        class="mb-4"
                        @finish="verifyOtp"
                      />

                      <v-alert
                        v-if="otpError"
                        type="error"
                        variant="tonal"
                        density="compact"
                        class="mb-3"
                      >{{ otpError }}</v-alert>

                      <v-btn
                        color="primary"
                        size="large"
                        block
                        :loading="verifyingOtp"
                        :disabled="otpCode.length < 6"
                        @click="verifyOtp"
                      >
                        <v-icon start>mdi-login</v-icon>
                        Verify & Sign In
                      </v-btn>

                      <v-btn
                        variant="text"
                        size="small"
                        block
                        class="mt-2"
                        :disabled="sendingOtp"
                        @click="resendOtp"
                      >Resend OTP</v-btn>
                    </div>
                  </v-tabs-window-item>
                </v-tabs-window>
              </v-card-text>
            </v-card>

            <p class="text-center text-caption text-medium-emphasis mt-4">
              © {{ new Date().getFullYear() }} Varanbook. All rights reserved.
            </p>
            <p class="text-center mt-2">
              <router-link
                to="/privacy-policy"
                class="text-caption text-medium-emphasis text-decoration-none"
                style="opacity: 0.8;"
              >Privacy Policy</router-link>
            </p>
          </v-col>
        </v-row>
      </v-container>
    </v-main>

    <!-- Error dialog -->
    <v-dialog v-model="errorDialog" max-width="360" persistent>
      <v-card rounded="xl">
        <v-card-title class="text-h6 pt-5 px-6">Sign In Failed</v-card-title>
        <v-card-text class="px-6 pb-4">{{ errorMessage }}</v-card-text>
        <v-card-actions class="px-6 pb-5 justify-end">
          <v-btn color="primary" variant="flat" min-width="80" @click="errorDialog = false">OK</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-app>
</template>

<script lang="ts" setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useHead } from '@unhead/vue'

useHead({
  title: 'Sign In — Varanbook',
  meta: [
    { name: 'description', content: 'Sign in to your Varanbook matrimonial centre account.' },
    { name: 'robots', content: 'noindex, nofollow' },
  ],
})
import { useAuthStore } from '@/stores/auth'
import {
  RecaptchaVerifier,
  signInWithPhoneNumber,
  type ConfirmationResult,
} from 'firebase/auth'
import { getAuth } from 'firebase/auth'
import { firebaseApp } from '@/plugins/firebase'
import axios from 'axios'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const firebaseAuth = getAuth(firebaseApp)

// ── Tab ───────────────────────────────────────────────────────────────────────
const tab = ref<'email' | 'otp'>('email')

// ── Email/password state ──────────────────────────────────────────────────────
const emailFormRef = ref()
const emailValid = ref(false)
const email = ref('')
const password = ref('')
const showPwd = ref(false)

// ── OTP state ─────────────────────────────────────────────────────────────────
const phone = ref('')
const otpCode = ref('')
const otpSent = ref(false)
const sendingOtp = ref(false)
const verifyingOtp = ref(false)
const otpError = ref('')
const phoneError = ref('')
let confirmationResult: ConfirmationResult | null = null
let recaptchaVerifier: RecaptchaVerifier | null = null

const isPhoneValid = computed(() => /^\+[1-9]\d{6,14}$/.test(phone.value))

// ── Shared error dialog ───────────────────────────────────────────────────────
const errorDialog = ref(false)
const errorMessage = ref('')

const rules = {
  required: (v: string) => !!v || 'Required',
  email: (v: string) => /.+@.+\..+/.test(v) || 'Enter a valid email',
}

// ── Email login ───────────────────────────────────────────────────────────────
async function handleEmailLogin() {
  const { valid: ok } = await emailFormRef.value.validate()
  if (!ok) return
  try {
    await auth.login({ email: email.value, password: password.value })
    if (auth.isAuthenticated) {
      router.push((route.query.redirect as string) || '/dashboard')
    }
  } catch (e: unknown) {
    errorMessage.value =
      axios.isAxiosError(e) && e.response?.status === 401
        ? 'Invalid credentials. Please check your email and password.'
        : 'Something went wrong. Please try again.'
    errorDialog.value = true
    auth.error = null
  }
}

// ── OTP: send ─────────────────────────────────────────────────────────────────
async function sendOtp() {
  phoneError.value = ''
  sendingOtp.value = true
  try {
    if (recaptchaVerifier) {
      recaptchaVerifier.clear()
      recaptchaVerifier = null
    }
    recaptchaVerifier = new RecaptchaVerifier(firebaseAuth, 'recaptcha-container', { size: 'invisible' })
    confirmationResult = await signInWithPhoneNumber(firebaseAuth, phone.value, recaptchaVerifier)
    otpSent.value = true
  } catch (err: any) {
    phoneError.value = getOtpError(err)
  } finally {
    sendingOtp.value = false
  }
}

// ── OTP: resend ───────────────────────────────────────────────────────────────
async function resendOtp() {
  otpCode.value = ''
  otpError.value = ''
  otpSent.value = false
  await sendOtp()
}

// ── OTP: verify & login ───────────────────────────────────────────────────────
async function verifyOtp() {
  if (!confirmationResult || otpCode.value.length < 6) return
  otpError.value = ''
  verifyingOtp.value = true
  try {
    const credential = await confirmationResult.confirm(otpCode.value)
    const idToken = await credential.user.getIdToken()
    await auth.loginOtp(phone.value, idToken)
    router.push((route.query.redirect as string) || '/dashboard')
  } catch (err: any) {
    otpError.value = getOtpError(err)
    otpCode.value = ''
  } finally {
    verifyingOtp.value = false
  }
}

function resetOtp() {
  otpSent.value = false
  otpCode.value = ''
  otpError.value = ''
  confirmationResult = null
}

function getOtpError(err: any): string {
  const code = err?.code as string | undefined
  if (code === 'auth/invalid-verification-code') return 'Incorrect OTP. Please try again.'
  if (code === 'auth/code-expired') return 'OTP has expired. Please request a new one.'
  if (code === 'auth/invalid-phone-number') return 'Invalid phone number format.'
  if (code === 'auth/billing-not-enabled') return 'Phone OTP is not available right now.'
  if (code === 'auth/too-many-requests') return 'Too many attempts. Please wait and try again.'
  // Backend 404 = no account with this phone
  if (axios.isAxiosError(err) && err.response?.status === 404)
    return 'No account found for this phone number.'
  return err?.message || 'OTP verification failed.'
}
</script>
