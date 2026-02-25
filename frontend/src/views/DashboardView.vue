<template>
  <div>
    <!-- Welcome Banner -->
    <v-row class="mb-6">
      <v-col>
        <v-card color="primary" rounded="xl" class="pa-6 text-white">
          <div class="d-flex align-center flex-wrap gap-4">
            <v-icon size="48" class="opacity-75">mdi-heart-circle</v-icon>
            <div>
              <h1 class="text-h5 font-weight-bold">
                Welcome back, {{ firstName }}!
              </h1>
              <p class="text-body-2 opacity-80 mb-0">
                Discover your perfect match today.
              </p>
            </div>
            <v-spacer />
            <v-btn
              color="white"
              variant="elevated"
              prepend-icon="mdi-account-group"
              @click="router.push('/profiles')"
            >
              Browse Profiles
            </v-btn>
          </div>
        </v-card>
      </v-col>
    </v-row>

    <!-- Stat Cards -->
    <v-row>
      <v-col
        v-for="stat in stats"
        :key="stat.label"
        cols="12"
        sm="6"
        lg="3"
      >
        <v-card rounded="xl" :color="stat.color" variant="tonal">
          <v-card-text class="d-flex align-center gap-4 pa-5">
            <v-icon :color="stat.iconColor" size="36">{{ stat.icon }}</v-icon>
            <div>
              <p class="text-body-2 text-medium-emphasis mb-0">{{ stat.label }}</p>
              <p class="text-h5 font-weight-bold mb-0">{{ stat.value }}</p>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Quick Actions -->
    <v-row class="mt-4">
      <v-col cols="12">
        <h2 class="text-h6 font-weight-semibold mb-4">Quick Actions</h2>
      </v-col>
      <v-col
        v-for="action in quickActions"
        :key="action.title"
        cols="12"
        sm="6"
        md="4"
      >
        <v-card
          rounded="xl"
          hover
          class="cursor-pointer"
          @click="router.push(action.to)"
        >
          <v-card-text class="d-flex align-center gap-4 pa-5">
            <v-avatar color="primary" variant="tonal" size="44">
              <v-icon :icon="action.icon" />
            </v-avatar>
            <div>
              <p class="font-weight-semibold mb-0">{{ action.title }}</p>
              <p class="text-body-2 text-medium-emphasis mb-0">{{ action.subtitle }}</p>
            </div>
            <v-spacer />
            <v-icon color="medium-emphasis">mdi-chevron-right</v-icon>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script lang="ts" setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

const firstName = computed(() => auth.user?.name?.split(' ')[0] ?? 'User')

const stats = [
  { label: 'Profiles Viewed', value: '—', icon: 'mdi-eye', color: 'blue', iconColor: 'blue' },
  { label: 'Shortlisted', value: '—', icon: 'mdi-heart', color: 'pink', iconColor: 'pink' },
  { label: 'Interests Sent', value: '—', icon: 'mdi-send', color: 'purple', iconColor: 'purple' },
  { label: 'Profile Complete', value: '—', icon: 'mdi-check-circle', color: 'green', iconColor: 'green' },
]

const quickActions = [
  { title: 'Browse Profiles', subtitle: 'Find your match', icon: 'mdi-account-group', to: '/profiles' },
  { title: 'Edit My Profile', subtitle: 'Keep your info updated', icon: 'mdi-account-edit', to: '/my-profile' },
  { title: 'Shortlist', subtitle: 'View saved profiles', icon: 'mdi-heart-outline', to: '/profiles' },
]
</script>
