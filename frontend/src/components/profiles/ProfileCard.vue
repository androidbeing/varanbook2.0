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
        {{ profile.display_name }}
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

      <!-- Occupation -->
      <div v-if="(profile as Profile).occupation" class="d-flex align-center gap-1 mt-1">
        <v-icon size="14" color="medium-emphasis">mdi-briefcase-outline</v-icon>
        <span class="text-caption text-medium-emphasis text-truncate">
          {{ (profile as Profile).occupation }}
        </span>
      </div>
    </v-card-text>
  </v-card>
</template>

<script lang="ts" setup>
import { computed } from 'vue'
import type { Profile } from '@/types'

const props = defineProps<{ profile: Profile }>()
const emit = defineEmits<{ click: [] }>()

const ageLine = computed(() => {
  const parts: string[] = []
  if (props.profile.date_of_birth) {
    const age = Math.floor(
      (Date.now() - new Date(props.profile.date_of_birth).getTime()) /
        (365.25 * 24 * 3600 * 1000),
    )
    parts.push(`${age} yrs`)
  }
  if (props.profile.gender) {
    parts.push(props.profile.gender.charAt(0).toUpperCase() + props.profile.gender.slice(1))
  }
  return parts.join(' · ') || '—'
})
</script>
