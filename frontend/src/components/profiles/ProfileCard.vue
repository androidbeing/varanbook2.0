<template>
  <v-card
    rounded="xl"
    hover
    class="cursor-pointer h-100"
    @click="emit('click')"
  >
    <!-- Profile Photo -->
    <div class="photo-wrapper rounded-t-xl" style="height:200px;overflow:hidden;position:relative;">
      <!-- Actual photo -->
      <v-img
        v-if="photoUrl"
        :src="photoUrl"
        height="200"
        cover
        position="top center"
        class="rounded-t-xl"
      />
      <!-- Placeholder when no photo / not visible -->
      <div
        v-else
        class="d-flex align-center justify-center bg-grey-lighten-3 rounded-t-xl"
        style="height:200px"
      >
        <v-icon size="80" color="grey-lighten-1">mdi-account-circle</v-icon>
      </div>

      <!-- Status badge (always on top) -->
      <v-chip
        :color="profile.status === 'active' ? 'success' : 'warning'"
        size="x-small"
        style="position:absolute;top:8px;right:8px;z-index:1"
      >
        {{ profile.status }}
      </v-chip>
    </div>

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

// photoUrl is resolved by the parent (ProfilesView) and passed in as a prop
// to avoid firing one HTTP request per card on mount.
const props = defineProps<{ profile: Profile; photoUrl?: string | null }>()
const emit = defineEmits<{ click: [] }>()

function fmtLabel(v: string | null | undefined): string {
  if (!v) return '—'
  return v.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

// ── Age (calculated from date_of_birth only) ─────────────────────────────────
const ageLine = computed(() => {
  const parts: string[] = []
  if (props.profile.date_of_birth) {
    const d = new Date(props.profile.date_of_birth)
    const t = new Date()
    let age = t.getFullYear() - d.getFullYear()
    if (t.getMonth() < d.getMonth() || (t.getMonth() === d.getMonth() && t.getDate() < d.getDate())) age--
    // Only display if the age is within a plausible matrimonial range
    if (age >= 18 && age <= 80) {
      parts.push(`${age} yrs`)
    }
  }
  if (props.profile.gender) {
    parts.push(props.profile.gender.charAt(0).toUpperCase() + props.profile.gender.slice(1))
  }
  return parts.join(' · ') || '—'
})
</script>
