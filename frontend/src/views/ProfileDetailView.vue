<template>
  <div>
    <div v-if="isPending" class="d-flex justify-center py-12">
      <v-progress-circular indeterminate color="primary" size="48" />
    </div>

    <v-alert v-else-if="isError" type="error" variant="tonal">
      Profile not found or you don't have permission to view it.
    </v-alert>

    <template v-else-if="profile">
      <v-btn
        prepend-icon="mdi-arrow-left"
        variant="text"
        class="mb-4"
        @click="router.back()"
      >
        Back
      </v-btn>

      <v-row>
        <!-- Photo + Basic Info -->
        <v-col cols="12" md="4">
          <v-card rounded="xl">
            <v-img
              :src="profile.profile_photo_url || '/placeholder-avatar.png'"
              height="300"
              cover
              class="rounded-t-xl"
            />
            <v-card-text class="text-center">
              <h2 class="text-h6 font-weight-bold">{{ profile.display_name }}</h2>
              <p class="text-body-2 text-medium-emphasis">
                {{ ageLabel }} &bull; {{ profile.city ?? '—' }}, {{ profile.state ?? '' }}
              </p>
              <v-chip
                :color="profile.status === 'active' ? 'success' : 'warning'"
                size="small"
                class="mt-1"
              >
                {{ profile.status }}
              </v-chip>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- Details -->
        <v-col cols="12" md="8">
          <v-card rounded="xl">
            <v-card-title class="pa-6 pb-2">About</v-card-title>
            <v-card-text class="pa-6 pt-2">
              <p v-if="profile.about_me" class="text-body-1 mb-6">{{ profile.about_me }}</p>
              <p v-else class="text-medium-emphasis text-body-2 mb-6">No bio provided.</p>

              <v-divider class="mb-4" />

              <v-row dense>
                <v-col
                  v-for="detail in details"
                  :key="detail.label"
                  cols="12"
                  sm="6"
                >
                  <div class="mb-3">
                    <p class="text-caption text-medium-emphasis mb-0">{{ detail.label }}</p>
                    <p class="text-body-1 font-weight-medium mb-0">{{ detail.value || '—' }}</p>
                  </div>
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </template>
  </div>
</template>

<script lang="ts" setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useQuery } from '@tanstack/vue-query'
import { profilesApi } from '@/api/profiles'

const props = defineProps<{ id: string }>()
const router = useRouter()

const { data: profile, isPending, isError } = useQuery({
  queryKey: computed(() => ['profile', props.id]),
  queryFn: () => profilesApi.get(props.id),
})

const ageLabel = computed(() => {
  if (!profile.value?.date_of_birth) return '—'
  const age = Math.floor(
    (Date.now() - new Date(profile.value.date_of_birth).getTime()) /
      (365.25 * 24 * 3600 * 1000),
  )
  return `${age} yrs`
})

const details = computed(() => {
  const p = profile.value
  if (!p) return []
  return [
    { label: 'Gender', value: p.gender },
    { label: 'Marital Status', value: p.marital_status },
    { label: 'Religion', value: p.religion },
    { label: 'Caste', value: p.caste },
    { label: 'Mother Tongue', value: p.mother_tongue },
    { label: 'Qualification', value: p.qualification },
    { label: 'Occupation', value: p.occupation },
    { label: 'Income Range', value: p.income_range },
    { label: 'Height', value: p.height_cm ? `${p.height_cm} cm` : null },
  ]
})
</script>
