<template>
  <div>
    <h1 class="text-h5 font-weight-bold mb-2">Browse Profiles</h1>
    <p class="text-body-2 text-medium-emphasis mb-6">
      Discover compatible matches from our community.
    </p>

    <!-- Filters -->
    <v-card rounded="xl" class="mb-6">
      <v-card-text>
        <v-row dense>
          <v-col cols="12" sm="4" md="3">
            <v-select
              v-model="filters.dhosam"
              label="Dhosam"
              :items="dhosamOptions"
              variant="outlined"
              density="compact"
              clearable
              hide-details
            />
          </v-col>
          <v-col cols="12" sm="4" md="3">
            <v-text-field
              v-model="filters.city"
              label="City"
              variant="outlined"
              density="compact"
              clearable
              hide-details
            />
          </v-col>
          <v-col cols="12" sm="4" md="3">
            <v-text-field
              v-model="searchText"
              label="Search by name"
              variant="outlined"
              density="compact"
              prepend-inner-icon="mdi-magnify"
              clearable
              hide-details
            />
          </v-col>
          <v-col cols="12" md="3" class="d-flex align-center">
            <v-btn color="primary" block @click="applyFilters">
              Apply Filters
            </v-btn>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- Results -->
    <div v-if="isPending" class="d-flex justify-center py-12">
      <v-progress-circular indeterminate color="primary" size="48" />
    </div>

    <v-alert v-else-if="isError" type="error" variant="tonal" class="mb-4">
      Failed to load profiles. Please try again.
    </v-alert>

    <!-- Caste-lock: member has no caste set -->
    <v-alert v-else-if="casteMissing" type="warning" variant="tonal" class="mb-4" prominent>
      <template #prepend>
        <v-icon size="36">mdi-lock-alert</v-icon>
      </template>
      <div class="text-subtitle-1 font-weight-semibold mb-1">Caste not set</div>
      <div class="text-body-2">
        Your centre has enabled caste-based profile filtering. Please set your caste in
        <router-link to="/my-profile" class="text-primary font-weight-semibold">My Profile</router-link>
        to browse matching profiles.
      </div>
    </v-alert>

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
            :shortlisted="shortlistStore.isShortlisted(profile.id)"
            @click="goToProfile(profile.id)"
            @shortlist="handleShortlist(profile.id)"
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

    <div v-else class="text-center py-12 text-medium-emphasis">
      <v-icon size="64" class="mb-4">mdi-account-search</v-icon>
      <p class="text-h6">No profiles found</p>
      <p class="text-body-2">Try adjusting your filters.</p>
    </div>

    <!-- Snackbar feedback for shortlist toggle -->
    <v-snackbar v-model="snackbar" :color="snackColor" timeout="2500" location="bottom end">
      {{ snackText }}
    </v-snackbar>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, watch, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useQuery, useQueryClient } from '@tanstack/vue-query'
import { profilesApi, filesApi } from '@/api/profiles'
import { useAuthStore } from '@/stores/auth'
import { useShortlistStore } from '@/stores/shortlist'
import ProfileCard from '@/components/profiles/ProfileCard.vue'
import type { Profile } from '@/types'

const router = useRouter()
const auth = useAuthStore()
const shortlistStore = useShortlistStore()
const qc = useQueryClient()

// Seed the shortlist store so heart icons reflect correct state
shortlistStore.init()

const snackbar = ref(false)
const snackText = ref('')
const snackColor = ref<'error' | 'success'>('success')

const page = ref(1)
const pageSize = 12
const searchText = ref('')
const filters = ref({ dhosam: '', city: '' })
const activeFilters = ref({ dhosam: '', city: '', search: '' })

// Map of profile.id → presigned GET URL for the first photo_key
const photoUrls = reactive<Record<string, string>>({})

const dhosamOptions = [
  { title: 'None',     value: 'none' },
  { title: 'Chevvai',  value: 'chevvai' },
  { title: 'Rahu',     value: 'rahu' },
  { title: 'Kethu',    value: 'kethu' },
  { title: 'Shani',    value: 'shani' },
  { title: 'Multiple', value: 'multiple' },
]

const { data, isPending, isError } = useQuery({
  queryKey: computed(() => ['profiles', page.value, activeFilters.value]),
  queryFn: () =>
    profilesApi.list({
      page: page.value,
      size: pageSize,
      dhosam: activeFilters.value.dhosam || undefined,
      city: activeFilters.value.city || undefined,
      search: activeFilters.value.search || undefined,
    }),
})

const profiles = computed<Profile[]>(() => data.value?.items ?? [])
const totalPages = computed(() => data.value?.pages ?? 1)
const casteMissing = computed(() => data.value?.caste_missing === true)

// Whenever the profile list OR the current user changes, re-fetch all presigned
// photo URLs. Watching auth.user ensures the block re-runs after fetchMe()
// resolves (fixing the race where isAdmin is false at immediate-watch time).
watch([profiles, () => auth.user], async ([list]) => {
  const fetches = (list as Profile[])
    .filter((p) => {
      if (!p.photo_keys?.length) return false
      const isOwn = auth.user?.id === p.user_id
      return auth.isAdmin || auth.isSuperAdmin || isOwn || p.photo_visible
    })
    .map(async (p) => {
      const key = p.photo_keys![0]
      if (photoUrls[p.id]) return       // already fetched
      try {
        const { url } = await filesApi.presignGet(key)
        photoUrls[p.id] = url
      } catch {
        // leave undefined → card shows placeholder
      }
    })
  await Promise.allSettled(fetches)
}, { immediate: true, deep: false })

function applyFilters() {
  page.value = 1
  activeFilters.value = {
    dhosam: filters.value.dhosam,
    city: filters.value.city,
    search: searchText.value,
  }
}

function goToProfile(id: string) {
  router.push(`/profiles/${id}`)
}

async function handleShortlist(profileId: string) {
  try {
    const added = await shortlistStore.toggle(profileId)
    await qc.invalidateQueries({ queryKey: ['shortlisted-profiles'] })
    snackText.value = added ? 'Added to shortlist' : 'Removed from shortlist'
    snackColor.value = 'success'
  } catch {
    snackText.value = 'Failed to update shortlist. Please try again.'
    snackColor.value = 'error'
  }
  snackbar.value = true
}

watch(page, () => window.scrollTo({ top: 0, behavior: 'smooth' }))
</script>
