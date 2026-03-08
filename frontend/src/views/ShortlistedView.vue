<template>
  <div>
    <h1 class="text-h5 font-weight-bold mb-2">Shortlisted Profiles</h1>
    <p class="text-body-2 text-medium-emphasis mb-6">
      Profiles you've shortlisted – revisit and connect at any time.
    </p>

    <!-- Loading -->
    <div v-if="isPending" class="d-flex justify-center py-12">
      <v-progress-circular indeterminate color="primary" size="48" />
    </div>

    <!-- Error -->
    <v-alert v-else-if="isError" type="error" variant="tonal" class="mb-4">
      Failed to load shortlisted profiles. Please try again.
    </v-alert>

    <!-- Results -->
    <template v-else-if="profiles.length">
      <v-row>
        <v-col
          v-for="profile in profiles"
          :key="profile.id"
          cols="12"
          sm="6"
          md="4"
          lg="3"
        >
          <ProfileCard
            :profile="profile"
            :photo-url="photoUrls[profile.id] ?? null"
            :shortlisted="true"
            @click="goToProfile(profile.id)"
            @shortlist="handleRemove(profile.id)"
          />
        </v-col>
      </v-row>

      <!-- Pagination -->
      <div class="d-flex justify-center mt-6">
        <v-pagination
          v-model="page"
          :length="totalPages"
          :total-visible="5"
          color="primary"
        />
      </div>
    </template>

    <!-- Empty state -->
    <div v-else class="text-center py-12 text-medium-emphasis">
      <v-icon size="64" class="mb-4">mdi-heart-outline</v-icon>
      <p class="text-h6">No shortlisted profiles yet</p>
      <p class="text-body-2 mb-6">Browse profiles and tap the heart to save them here.</p>
      <v-btn color="primary" prepend-icon="mdi-account-group" @click="router.push('/profiles')">
        Browse Profiles
      </v-btn>
    </div>

    <!-- Snackbar feedback -->
    <v-snackbar v-model="snackbar" :color="snackColor" timeout="2500" location="bottom end">
      {{ snackText }}
    </v-snackbar>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, watch, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useQuery, useQueryClient } from '@tanstack/vue-query'
import { shortlistApi } from '@/api/shortlist'
import { filesApi } from '@/api/profiles'
import { useAuthStore } from '@/stores/auth'
import { useShortlistStore } from '@/stores/shortlist'
import ProfileCard from '@/components/profiles/ProfileCard.vue'
import type { Profile } from '@/types'

const router = useRouter()
const auth = useAuthStore()
const shortlistStore = useShortlistStore()
const qc = useQueryClient()

const page = ref(1)
const pageSize = 12
const photoUrls = reactive<Record<string, string>>({})

const snackbar = ref(false)
const snackText = ref('')
const snackColor = ref<'error' | 'success'>('success')

// Ensure the shortlist store is seeded
shortlistStore.init()

const { data, isPending, isError } = useQuery({
  queryKey: computed(() => ['shortlisted-profiles', page.value]),
  queryFn: () => shortlistApi.shortlistedProfiles(page.value, pageSize),
})

const profiles = computed<Profile[]>(() => data.value?.items ?? [])
const totalPages = computed(() => data.value?.pages ?? 1)

// Fetch presigned photo URLs whenever the profile list changes
watch([profiles, () => auth.user], async ([list]) => {
  const fetches = (list as Profile[])
    .filter((p) => {
      if (!p.photo_keys?.length) return false
      const isOwn = auth.user?.id === p.user_id
      return auth.isAdmin || auth.isSuperAdmin || isOwn || p.photo_visible
    })
    .map(async (p) => {
      const key = p.photo_keys![0]
      if (photoUrls[p.id]) return
      try {
        const { url } = await filesApi.presignGet(key)
        photoUrls[p.id] = url
      } catch {
        // leave undefined → card shows placeholder
      }
    })
  await Promise.allSettled(fetches)
}, { immediate: true, deep: false })

async function handleRemove(profileId: string) {
  try {
    await shortlistStore.toggle(profileId)
    // Invalidate so the grid refreshes without the removed profile
    await qc.invalidateQueries({ queryKey: ['shortlisted-profiles'] })
    snackText.value = 'Removed from shortlist'
    snackColor.value = 'success'
  } catch {
    snackText.value = 'Failed to remove. Please try again.'
    snackColor.value = 'error'
  }
  snackbar.value = true
}

function goToProfile(id: string) {
  router.push(`/profiles/${id}`)
}

watch(page, () => window.scrollTo({ top: 0, behavior: 'smooth' }))
</script>
