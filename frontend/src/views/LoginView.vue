<template>
  <v-app>
    <v-main class="bg-background">
      <v-container class="fill-height" fluid>
        <v-row align="center" justify="center" style="min-height: 100vh">
          <v-col cols="12" sm="8" md="5" lg="4">
            <!-- Logo/Branding -->
            <div class="text-center mb-8">
              <h1 class="text-h4 font-weight-bold text-primary mt-2">Varanbook</h1>
              <p class="text-body-2 text-medium-emphasis">Find your perfect match</p>
            </div>

            <v-card elevation="4" rounded="xl" class="pa-2">
              <v-card-text class="pa-6">
                <h2 class="text-h6 font-weight-semibold mb-6 text-center">Sign In</h2>

                <v-form ref="formRef" v-model="valid" @submit.prevent="handleLogin">
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

                  <div class="text-right mb-3">
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
                    :disabled="!valid"
                    class="mt-2"
                  >
                    Sign In
                  </v-btn>
                </v-form>
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

    <!-- Login error dialog -->
    <v-dialog v-model="errorDialog" max-width="360" persistent>
      <v-card rounded="xl">
        <v-card-title class="text-h6 pt-5 px-6">Login Failed</v-card-title>
        <v-card-text class="px-6 pb-4">{{ errorMessage }}</v-card-text>
        <v-card-actions class="px-6 pb-5 justify-end">
          <v-btn color="primary" variant="flat" min-width="80" @click="errorDialog = false">OK</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-app>
</template>

<script lang="ts" setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import axios from 'axios'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const formRef = ref()
const valid = ref(false)
const email = ref('')
const password = ref('')
const showPwd = ref(false)
const errorDialog = ref(false)
const errorMessage = ref('')

const rules = {
  required: (v: string) => !!v || 'Required',
  email: (v: string) => /.+@.+\..+/.test(v) || 'Enter a valid email',
}

async function handleLogin() {
  const { valid: ok } = await formRef.value.validate()
  if (!ok) return
  try {
    await auth.login({ email: email.value, password: password.value })
    if (auth.isAuthenticated) {
      const redirect = (route.query.redirect as string) || '/'
      router.push(redirect)
    }
  } catch (e: unknown) {
    if (axios.isAxiosError(e) && e.response?.status === 401) {
      errorMessage.value = 'Invalid credentials. Please check your email and password.'
    } else {
      errorMessage.value = 'Something went wrong. Please try again.'
    }
    errorDialog.value = true
    auth.error = null
  }
}
</script>
