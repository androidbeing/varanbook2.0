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

                    <v-text-field
                      v-model="form.phone"
                      label="Phone (optional)"
                      prepend-inner-icon="mdi-phone"
                      variant="outlined"
                      density="comfortable"
                      :rules="[rules.optionalPhone]"
                      class="mb-3"
                      placeholder="+919876543210"
                      autocomplete="tel"
                    />

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
                      :disabled="!valid"
                    >
                      Create Account
                    </v-btn>
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
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { publicApi } from '@/api/public'
import type { TenantPublicInfo } from '@/types'

const route = useRoute()
const slug = route.params.slug as string

// State
const loading = ref(true)
const notFound = ref(false)
const tenantInfo = ref<TenantPublicInfo | null>(null)
const logoUrl = ref<string | null>(null)
const registered = ref(false)
const submitting = ref(false)
const errorMsg = ref('')
const formRef = ref()
const valid = ref(false)
const showPwd = ref(false)
const confirmPassword = ref('')

const form = ref({
  full_name: '',
  email: '',
  phone: '',
  gender: '' as 'male' | 'female' | '',
  password: '',
})

// Validation rules
const rules = {
  required: (v: string) => !!v || 'Required',
  minLen: (n: number) => (v: string) => v.length >= n || `Min ${n} characters`,
  email: (v: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v) || 'Invalid email',
  optionalPhone: (v: string) =>
    !v || /^\+[1-9]\d{6,14}$/.test(v) || 'E.164 format required, e.g. +919876543210',
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

// Load tenant info
onMounted(async () => {
  try {
    tenantInfo.value = await publicApi.getTenant(slug)
    // Resolve logo URL if present
    if (tenantInfo.value.logo_key) {
      try {
        // Use the public-friendly presign endpoint or build S3 URL
        // For now, we'll try to get a presigned URL via the API
        const { filesApi } = await import('@/api/profiles')
        const { url } = await filesApi.presignGet(tenantInfo.value.logo_key)
        logoUrl.value = url
      } catch {
        // Logo not accessible without auth — that's fine, skip it
      }
    }
  } catch {
    notFound.value = true
  } finally {
    loading.value = false
  }
})

// Submit registration
async function handleRegister() {
  const { valid: isValid } = await formRef.value.validate()
  if (!isValid) return

  submitting.value = true
  errorMsg.value = ''
  try {
    await publicApi.register(slug, {
      full_name: form.value.full_name,
      email: form.value.email,
      phone: form.value.phone || undefined,
      gender: form.value.gender as 'male' | 'female',
      password: form.value.password,
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
