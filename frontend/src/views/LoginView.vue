<template>
  <v-app>
    <v-main class="bg-background">
      <v-container class="fill-height" fluid>
        <v-row align="center" justify="center" style="min-height: 100vh">
          <v-col cols="12" sm="8" md="5" lg="4">
            <!-- Logo/Branding -->
            <div class="text-center mb-8">
              <v-icon color="primary" size="56">mdi-heart-circle</v-icon>
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

                  <v-alert
                    v-if="auth.error"
                    type="error"
                    variant="tonal"
                    density="compact"
                    class="mb-4"
                    closable
                    @click:close="auth.error = null"
                  >
                    {{ auth.error }}
                  </v-alert>

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

            <p class="text-center text-caption text-medium-emphasis mt-6">
              © {{ new Date().getFullYear() }} Varanbook. All rights reserved.
            </p>
          </v-col>
        </v-row>
      </v-container>
    </v-main>
  </v-app>
</template>

<script lang="ts" setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const formRef = ref()
const valid = ref(false)
const email = ref('')
const password = ref('')
const showPwd = ref(false)

const rules = {
  required: (v: string) => !!v || 'Required',
  email: (v: string) => /.+@.+\..+/.test(v) || 'Enter a valid email',
}

async function handleLogin() {
  const { valid: ok } = await formRef.value.validate()
  if (!ok) return
  await auth.login({ email: email.value, password: password.value })
  if (auth.isAuthenticated) {
    const redirect = (route.query.redirect as string) || '/'
    router.push(redirect)
  }
}
</script>
