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
          <ProfileCard :profile="profile" @click="goToProfile(profile.id)" />
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
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useQuery } from '@tanstack/vue-query'
import { profilesApi } from '@/api/profiles'
import ProfileCard from '@/components/profiles/ProfileCard.vue'
import type { Profile } from '@/types'

const router = useRouter()

const page = ref(1)
const pageSize = 12
const searchText = ref('')
const filters = ref({ dhosam: '', city: '' })
const activeFilters = ref({ dhosam: '', city: '', search: '' })

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

watch(page, () => window.scrollTo({ top: 0, behavior: 'smooth' }))
</script>
