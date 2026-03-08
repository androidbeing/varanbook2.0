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
                <h2 class="text-h6 font-weight-semibold mb-2 text-center">Forgot Password</h2>
                <p class="text-body-2 text-medium-emphasis text-center mb-6">
                  Enter the email address linked to your account and we'll send you a reset link.
                </p>

                <v-form ref="formRef" v-model="valid" @submit.prevent="handleSubmit">
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
                    :loading="loading"
                    :disabled="!valid"
                  >
                    Send Reset Link
                  </v-btn>
                </v-form>

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

    <!-- Success dialog -->
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

    <!-- Error dialog -->
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
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { authApi } from '@/api/auth'

const router = useRouter()

const formRef = ref()
const valid = ref(false)
const email = ref('')
const loading = ref(false)
const successDialog = ref(false)
const errorDialog = ref(false)

const rules = {
  required: (v: string) => !!v || 'Required',
  email: (v: string) => /.+@.+\..+/.test(v) || 'Enter a valid email',
}

async function handleSubmit() {
  const { valid: ok } = await formRef.value.validate()
  if (!ok) return
  loading.value = true
  try {
    await authApi.requestPasswordReset(email.value)
    successDialog.value = true
  } catch {
    // Show error dialog — do NOT reveal whether the email exists
    errorDialog.value = true
  } finally {
    loading.value = false
  }
}

function goToLogin() {
  successDialog.value = false
  router.push('/login')
}
</script>
