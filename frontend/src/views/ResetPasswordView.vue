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
                <h2 class="text-h6 font-weight-semibold mb-2 text-center">Set New Password</h2>
                <p class="text-body-2 text-medium-emphasis text-center mb-6">
                  Enter your new password below.
                </p>

                <!-- Invalid / missing token state -->
                <v-alert
                  v-if="!token"
                  type="error"
                  variant="tonal"
                  density="compact"
                  class="mb-4"
                >
                  Invalid reset link. Please
                  <router-link to="/forgot-password" class="text-decoration-none font-weight-medium">
                    request a new one
                  </router-link>.
                </v-alert>

                <v-form v-else ref="formRef" v-model="valid" @submit.prevent="handleSubmit">
                  <v-text-field
                    v-model="password"
                    label="New password"
                    :type="showPwd ? 'text' : 'password'"
                    prepend-inner-icon="mdi-lock-outline"
                    :append-inner-icon="showPwd ? 'mdi-eye-off' : 'mdi-eye'"
                    @click:append-inner="showPwd = !showPwd"
                    variant="outlined"
                    density="comfortable"
                    :rules="[rules.required, rules.minLength]"
                    class="mb-3"
                    autocomplete="new-password"
                  />

                  <v-text-field
                    v-model="confirm"
                    label="Confirm new password"
                    :type="showConfirm ? 'text' : 'password'"
                    prepend-inner-icon="mdi-lock-check-outline"
                    :append-inner-icon="showConfirm ? 'mdi-eye-off' : 'mdi-eye'"
                    @click:append-inner="showConfirm = !showConfirm"
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
                    :loading="loading"
                    :disabled="!valid"
                  >
                    Reset Password
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
    <v-dialog v-model="successDialog" max-width="360" persistent>
      <v-card rounded="xl">
        <v-card-title class="text-h6 pt-5 px-6">Password Reset</v-card-title>
        <v-card-text class="px-6 pb-4">
          Your password has been updated successfully. You can now log in with your new password.
        </v-card-text>
        <v-card-actions class="px-6 pb-5 justify-end">
          <v-btn color="primary" variant="flat" min-width="80" @click="goToLogin">OK</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Error dialog -->
    <v-dialog v-model="errorDialog" max-width="380" persistent>
      <v-card rounded="xl">
        <v-card-title class="text-h6 pt-5 px-6">Reset Failed</v-card-title>
        <v-card-text class="px-6 pb-4">{{ errorMessage }}</v-card-text>
        <v-card-actions class="px-6 pb-5 justify-between">
          <v-btn variant="text" @click="router.push('/forgot-password')">Request new link</v-btn>
          <v-btn color="primary" variant="flat" min-width="80" @click="errorDialog = false">OK</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-app>
</template>

<script lang="ts" setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { authApi } from '@/api/auth'
import axios from 'axios'

const router = useRouter()
const route = useRoute()

const token = computed(() => (route.query.token as string) || '')

const formRef = ref()
const valid = ref(false)
const password = ref('')
const confirm = ref('')
const showPwd = ref(false)
const showConfirm = ref(false)
const loading = ref(false)
const successDialog = ref(false)
const errorDialog = ref(false)
const errorMessage = ref('')

const rules = {
  required: (v: string) => !!v || 'Required',
  minLength: (v: string) => v.length >= 8 || 'Minimum 8 characters',
  match: (v: string) => v === password.value || 'Passwords do not match',
}

async function handleSubmit() {
  const { valid: ok } = await formRef.value.validate()
  if (!ok) return
  loading.value = true
  try {
    await authApi.confirmPasswordReset(token.value, password.value)
    successDialog.value = true
  } catch (e: unknown) {
    if (axios.isAxiosError(e) && e.response?.status === 400) {
      errorMessage.value =
        'This reset link is invalid or has already been used. Please request a new one.'
    } else if (axios.isAxiosError(e) && e.response?.status === 410) {
      errorMessage.value = 'This reset link has expired. Please request a new one.'
    } else {
      errorMessage.value = 'Something went wrong. Please try again later.'
    }
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
