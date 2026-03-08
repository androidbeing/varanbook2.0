<template>
  <div>
    <v-row class="mb-6">
      <v-col>
        <v-card color="primary" rounded="xl" class="pa-6">
          <div class="d-flex align-center gap-4">
            <v-icon size="40" class="opacity-75">mdi-lock-reset</v-icon>
            <div>
              <h1 class="text-h5 font-weight-bold">Change Password</h1>
              <p class="text-body-2 opacity-80 mb-0">Update your account password.</p>
            </div>
          </div>
        </v-card>
      </v-col>
    </v-row>

    <v-row justify="start">
      <v-col cols="12" sm="10" md="6" lg="5">
        <v-card rounded="xl" elevation="2">
          <v-card-text class="pa-6">
            <v-form ref="formRef" v-model="valid" @submit.prevent="handleSubmit">
              <v-text-field
                v-model="fields.current_password"
                label="Current Password"
                variant="outlined"
                density="comfortable"
                :type="showCurrent ? 'text' : 'password'"
                :append-inner-icon="showCurrent ? 'mdi-eye-off' : 'mdi-eye'"
                @click:append-inner="showCurrent = !showCurrent"
                prepend-inner-icon="mdi-lock"
                :rules="[required]"
                class="mb-3"
              />
              <v-text-field
                v-model="fields.new_password"
                label="New Password"
                variant="outlined"
                density="comfortable"
                :type="showNew ? 'text' : 'password'"
                :append-inner-icon="showNew ? 'mdi-eye-off' : 'mdi-eye'"
                @click:append-inner="showNew = !showNew"
                prepend-inner-icon="mdi-lock-plus"
                :rules="[required, strengthRule]"
                hint="Min 8 chars, uppercase, lowercase, digit, special char"
                persistent-hint
                class="mb-3"
              />
              <v-text-field
                v-model="confirmPassword"
                label="Confirm New Password"
                variant="outlined"
                density="comfortable"
                :type="showNew ? 'text' : 'password'"
                prepend-inner-icon="mdi-lock-check"
                :rules="[required, matchRule]"
                class="mb-5"
              />
              <v-btn
                type="submit"
                color="warning"
                variant="elevated"
                size="large"
                block
                :loading="saving"
                :disabled="!valid"
              >
                Update Password
              </v-btn>
            </v-form>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-snackbar v-model="snack.show" :color="snack.color" timeout="3500" location="bottom right">
      {{ snack.message }}
    </v-snackbar>
  </div>
</template>

<script lang="ts" setup>
import { ref } from 'vue'
import client from '@/api/client'

const formRef = ref()
const valid = ref(false)
const saving = ref(false)
const showCurrent = ref(false)
const showNew = ref(false)
const fields = ref({ current_password: '', new_password: '' })
const confirmPassword = ref('')
const snack = ref({ show: false, color: 'success', message: '' })

const required = (v: string) => !!v || 'Required'
const strengthRule = (v: string) => {
  if (!v || v.length < 8) return 'Min 8 characters'
  if (!/[A-Z]/.test(v)) return 'Need at least one uppercase letter'
  if (!/[a-z]/.test(v)) return 'Need at least one lowercase letter'
  if (!/[0-9]/.test(v)) return 'Need at least one digit'
  if (!/[!@#$%^&*()\-_=+\[\]{}|;:,.<>?]/.test(v)) return 'Need at least one special character'
  return true
}
const matchRule = (v: string) => v === fields.value.new_password || 'Passwords do not match'

async function handleSubmit() {
  const { valid: ok } = await formRef.value.validate()
  if (!ok) return
  saving.value = true
  try {
    await client.post('/auth/change-password', {
      current_password: fields.value.current_password,
      new_password: fields.value.new_password,
    })
    snack.value = { show: true, color: 'success', message: 'Password changed successfully!' }
    fields.value = { current_password: '', new_password: '' }
    confirmPassword.value = ''
    formRef.value.reset()
  } catch (e: any) {
    const detail = e?.response?.data?.detail
    snack.value = {
      show: true,
      color: 'error',
      message: typeof detail === 'string' ? detail : 'Failed to change password. Please try again.',
    }
  } finally {
    saving.value = false
  }
}
</script>
