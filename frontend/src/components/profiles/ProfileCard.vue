<template>
  <v-card
    rounded="xl"
    hover
    class="cursor-pointer h-100"
    @click="emit('click')"
  >
    <!-- Profile Photo -->
    <v-img
      :src="profile.profile_photo_url || ''"
      height="200"
      cover
      class="rounded-t-xl"
    >
      <template #error>
        <div
          class="d-flex align-center justify-center h-100 bg-grey-lighten-3"
          style="height: 200px"
        >
          <v-icon size="72" color="grey">mdi-account-circle</v-icon>
        </div>
      </template>

      <!-- Status badge -->
      <v-chip
        :color="profile.status === 'active' ? 'success' : 'warning'"
        size="x-small"
        class="position-absolute"
        style="top: 8px; right: 8px"
      >
        {{ profile.status }}
      </v-chip>
    </v-img>

    <v-card-text class="pa-4">
      <!-- Name -->
      <p class="text-subtitle-1 font-weight-bold mb-0 text-truncate">
        {{ profile.full_name || (profile.gender === 'male' ? 'Male' : profile.gender === 'female' ? 'Female' : 'Member') }}
      </p>

      <!-- Age + Gender -->
      <p class="text-body-2 text-medium-emphasis mb-2">
        {{ ageLine }}
      </p>

      <!-- Location -->
      <div v-if="profile.city || profile.state" class="d-flex align-center gap-1">
        <v-icon size="14" color="medium-emphasis">mdi-map-marker-outline</v-icon>
        <span class="text-caption text-medium-emphasis text-truncate">
          {{ [profile.city, profile.state].filter(Boolean).join(', ') }}
        </span>
      </div>

      <!-- Profession -->
      <div v-if="profile.profession" class="d-flex align-center gap-1 mt-1">
        <v-icon size="14" color="medium-emphasis">mdi-briefcase-outline</v-icon>
        <span class="text-caption text-medium-emphasis text-truncate">
          {{ profile.profession }}
        </span>
      </div>

      <!-- Religion / Caste -->
      <div v-if="profile.religion || profile.caste" class="d-flex align-center gap-1 mt-1">
        <v-icon size="14" color="medium-emphasis">mdi-om</v-icon>
        <span class="text-caption text-medium-emphasis text-truncate">
          {{ [profile.religion, profile.caste].filter(Boolean).join(' · ') }}
        </span>
      </div>

      <!-- Key chips -->
      <div class="d-flex flex-wrap ga-1 mt-2">
        <v-chip v-if="profile.height_cm" size="x-small" variant="tonal">
          {{ profile.height_cm }} cm
        </v-chip>
        <v-chip v-if="profile.qualification" size="x-small" variant="tonal">
          {{ fmtLabel(profile.qualification) }}
        </v-chip>
        <v-chip v-if="profile.marital_status && profile.marital_status !== 'never_married'" size="x-small" variant="tonal" color="warning">
          {{ fmtLabel(profile.marital_status) }}
        </v-chip>
      </div>
    </v-card-text>
  </v-card>
</template>

<script lang="ts" setup>
import { computed } from 'vue'
import type { Profile } from '@/types'

const props = defineProps<{ profile: Profile }>()
const emit = defineEmits<{ click: [] }>()

function fmtLabel(v: string | null | undefined): string {
  if (!v) return '—'
  return v.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

const ageLine = computed(() => {
  const parts: string[] = []
  if (props.profile.date_of_birth) {
    const d = new Date(props.profile.date_of_birth)
    const t = new Date()
    let age = t.getFullYear() - d.getFullYear()
    if (t.getMonth() < d.getMonth() || (t.getMonth() === d.getMonth() && t.getDate() < d.getDate())) age--
    parts.push(`${age} yrs`)
  }
  if (props.profile.gender) {
    parts.push(props.profile.gender.charAt(0).toUpperCase() + props.profile.gender.slice(1))
  }
  return parts.join(' · ') || '—'
})
</script>
