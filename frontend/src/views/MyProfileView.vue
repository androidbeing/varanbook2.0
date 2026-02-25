<template>
  <div>
    <h1 class="text-h5 font-weight-bold mb-6">My Profile</h1>

    <div v-if="isPending" class="d-flex justify-center py-12">
      <v-progress-circular indeterminate color="primary" size="48" />
    </div>

    <v-form v-else ref="formRef" @submit.prevent="handleSave">
      <v-row>
        <!-- Photo Card -->
        <v-col cols="12" md="4" lg="3">
          <v-card rounded="xl" class="text-center pa-4">
            <v-avatar size="120" class="mb-4">
              <v-img
                :src="form.profile_photo_url || ''"
                :alt="form.display_name"
              >
                <template #error>
                  <v-icon size="80" color="medium-emphasis">mdi-account-circle</v-icon>
                </template>
              </v-img>
            </v-avatar>
            <p class="text-h6 font-weight-semibold mb-1">{{ form.display_name || 'Your Name' }}</p>
            <v-chip
              :color="profile?.status === 'active' ? 'success' : 'warning'"
              size="small"
              class="mb-4"
            >
              {{ profile?.status ?? 'draft' }}
            </v-chip>
          </v-card>
        </v-col>

        <!-- Edit Form -->
        <v-col cols="12" md="8" lg="9">
          <v-card rounded="xl">
            <v-card-text class="pa-6">
              <v-row>
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="form.display_name"
                    label="Display Name *"
                    variant="outlined"
                    density="comfortable"
                    :rules="[rules.required]"
                  />
                </v-col>
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="form.date_of_birth"
                    label="Date of Birth"
                    type="date"
                    variant="outlined"
                    density="comfortable"
                  />
                </v-col>
                <v-col cols="12" sm="6">
                  <v-select
                    v-model="form.gender"
                    label="Gender"
                    :items="genderOptions"
                    variant="outlined"
                    density="comfortable"
                  />
                </v-col>
                <v-col cols="12" sm="6">
                  <v-select
                    v-model="form.marital_status"
                    label="Marital Status"
                    :items="maritalOptions"
                    variant="outlined"
                    density="comfortable"
                  />
                </v-col>
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="form.religion"
                    label="Religion"
                    variant="outlined"
                    density="comfortable"
                  />
                </v-col>
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="form.caste"
                    label="Caste"
                    variant="outlined"
                    density="comfortable"
                  />
                </v-col>
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="form.city"
                    label="City"
                    variant="outlined"
                    density="comfortable"
                  />
                </v-col>
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="form.state"
                    label="State"
                    variant="outlined"
                    density="comfortable"
                  />
                </v-col>
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="form.occupation"
                    label="Occupation"
                    variant="outlined"
                    density="comfortable"
                  />
                </v-col>
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model.number="form.height_cm"
                    label="Height (cm)"
                    type="number"
                    variant="outlined"
                    density="comfortable"
                  />
                </v-col>
                <v-col cols="12">
                  <v-textarea
                    v-model="form.about_me"
                    label="About Me"
                    rows="3"
                    variant="outlined"
                    density="comfortable"
                    counter="500"
                    maxlength="500"
                  />
                </v-col>
              </v-row>

              <v-alert
                v-if="saveError"
                type="error"
                variant="tonal"
                density="compact"
                class="mb-4"
              >
                {{ saveError }}
              </v-alert>

              <v-btn
                type="submit"
                color="primary"
                size="large"
                :loading="saving"
                prepend-icon="mdi-content-save"
              >
                Save Changes
              </v-btn>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </v-form>

    <!-- Success Snackbar -->
    <v-snackbar v-model="snack" color="success" timeout="3000">
      Profile saved successfully!
    </v-snackbar>
  </div>
</template>

<script lang="ts" setup>
import { ref, watch } from 'vue'
import { useQuery, useQueryClient } from '@tanstack/vue-query'
import { profilesApi } from '@/api/profiles'
import type { Profile } from '@/types'

const qc = useQueryClient()
const formRef = ref()
const saving = ref(false)
const saveError = ref<string | null>(null)
const snack = ref(false)

const { data: profile, isPending } = useQuery({
  queryKey: ['my-profile'],
  queryFn: () => profilesApi.mine(),
  retry: false,
})

const form = ref<Partial<Profile>>({
  display_name: '',
  date_of_birth: null,
  gender: null,
  marital_status: null,
  religion: '',
  caste: '',
  city: '',
  state: '',
  occupation: '',
  height_cm: null,
  about_me: '',
})

watch(
  profile,
  (p) => {
    if (p) Object.assign(form.value, p)
  },
  { immediate: true },
)

const rules = { required: (v: string) => !!v || 'Required' }
const genderOptions = [
  { title: 'Male', value: 'male' },
  { title: 'Female', value: 'female' },
  { title: 'Other', value: 'other' },
]
const maritalOptions = [
  { title: 'Never Married', value: 'never_married' },
  { title: 'Divorced', value: 'divorced' },
  { title: 'Widowed', value: 'widowed' },
  { title: 'Annulled', value: 'annulled' },
]

async function handleSave() {
  const { valid } = await formRef.value.validate()
  if (!valid) return
  saving.value = true
  saveError.value = null
  try {
    if (profile.value) {
      await profilesApi.update(profile.value.id, form.value)
    } else {
      await profilesApi.create(form.value)
    }
    qc.invalidateQueries({ queryKey: ['my-profile'] })
    snack.value = true
  } catch (e) {
    saveError.value = 'Failed to save profile. Please try again.'
  } finally {
    saving.value = false
  }
}
</script>
