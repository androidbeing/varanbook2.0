<template>
  <div>
    <h1 class="text-h5 font-weight-bold mb-1">My Interests</h1>
    <p class="text-body-2 text-medium-emphasis mb-4">
      Track interests you've sent and respond to requests you've received.
    </p>

    <v-tabs v-model="tab" color="primary" class="mb-6">
      <v-tab value="sent">
        <v-icon start>mdi-heart-arrow</v-icon>
        Sent
        <v-chip v-if="sentTotal > 0" size="x-small" class="ml-2">{{ sentTotal }}</v-chip>
      </v-tab>
      <v-tab value="received">
        <v-icon start>mdi-heart-flash</v-icon>
        Received
        <v-chip v-if="pendingCount > 0" color="pink" size="x-small" class="ml-2">
          {{ pendingCount }}
        </v-chip>
      </v-tab>
    </v-tabs>

    <v-window v-model="tab">
      <!-- ── SENT TAB ──────────────────────────────────────────────────── -->
      <v-window-item value="sent">
        <!-- loading -->
        <div v-if="sentPending" class="d-flex justify-center py-12">
          <v-progress-circular indeterminate color="primary" size="48" />
        </div>

        <v-alert v-else-if="sentError" type="error" variant="tonal" class="mb-4">
          Failed to load sent interests.
        </v-alert>

        <template v-else-if="sentItems.length">
          <v-row>
            <v-col
              v-for="item in sentItems"
              :key="item.shortlist_id"
              cols="12"
              sm="6"
              md="4"
              lg="3"
            >
              <v-card
                rounded="xl"
                hover
                class="cursor-pointer h-100"
                @click="goToProfile(item.profile.id)"
              >
                <!-- Photo -->
                <div style="height:170px;overflow:hidden;position:relative;" class="rounded-t-xl">
                  <v-img
                    v-if="sentPhotoUrls[item.profile.id]"
                    :src="sentPhotoUrls[item.profile.id]"
                    height="170"
                    cover
                    position="top center"
                    class="rounded-t-xl"
                  />
                  <div
                    v-else
                    class="d-flex align-center justify-center bg-grey-lighten-3 rounded-t-xl"
                    style="height:170px"
                  >
                    <v-icon size="72" color="grey-lighten-1">mdi-account-circle</v-icon>
                  </div>

                  <!-- Status badge -->
                  <v-chip
                    :color="statusColor(item.status)"
                    size="x-small"
                    label
                    style="position:absolute;top:8px;right:8px;z-index:1"
                  >
                    {{ fmtLabel(item.status) }}
                  </v-chip>
                </div>

                <v-card-text class="pa-3">
                  <p class="text-subtitle-2 font-weight-bold mb-0 text-truncate">
                    {{ item.profile.full_name || genderLabel(item.profile.gender) }}
                  </p>
                  <p class="text-caption text-medium-emphasis mb-1">
                    {{ ageLine(item.profile) }}
                  </p>
                  <div v-if="item.profile.city || item.profile.state" class="d-flex align-center gap-1">
                    <v-icon size="12" color="medium-emphasis">mdi-map-marker-outline</v-icon>
                    <span class="text-caption text-medium-emphasis text-truncate">
                      {{ [item.profile.city, item.profile.state].filter(Boolean).join(', ') }}
                    </span>
                  </div>
                  <p v-if="item.note" class="text-caption text-medium-emphasis mt-1 mb-0 text-truncate">
                    <v-icon size="12">mdi-note-outline</v-icon> {{ item.note }}
                  </p>
                  <p class="text-caption text-disabled mt-1 mb-0">
                    Sent {{ fmtDate(item.created_at) }}
                  </p>
                </v-card-text>

                <!-- Withdraw button for pending only -->
                <v-card-actions v-if="item.status === 'shortlisted'" class="pt-0 px-3 pb-3">
                  <v-btn
                    size="small"
                    variant="tonal"
                    color="grey"
                    block
                    :loading="withdrawing[item.shortlist_id]"
                    @click.stop="withdraw(item.shortlist_id, item.profile.id)"
                  >
                    <v-icon start size="16">mdi-heart-broken</v-icon>
                    Withdraw Interest
                  </v-btn>
                </v-card-actions>
              </v-card>
            </v-col>
          </v-row>

          <div class="d-flex justify-center mt-6">
            <v-pagination v-model="sentPage" :length="sentPages" :total-visible="5" color="primary" />
          </div>
        </template>

        <div v-else class="text-center py-12 text-medium-emphasis">
          <v-icon size="64" class="mb-4">mdi-heart-arrow</v-icon>
          <p class="text-h6">No interests sent yet</p>
          <p class="text-body-2 mb-6">Browse profiles and tap the heart to express interest.</p>
          <v-btn color="primary" prepend-icon="mdi-account-group" @click="router.push('/profiles')">
            Browse Profiles
          </v-btn>
        </div>
      </v-window-item>

      <!-- ── RECEIVED TAB ──────────────────────────────────────────────── -->
      <v-window-item value="received">
        <!-- Status filter -->
        <div class="d-flex gap-2 flex-wrap mb-5">
          <v-chip
            v-for="opt in receivedFilters"
            :key="opt.value ?? 'all'"
            :color="receivedStatusFilter === opt.value ? 'primary' : undefined"
            :variant="receivedStatusFilter === opt.value ? 'flat' : 'tonal'"
            size="small"
            class="cursor-pointer"
            @click="applyReceivedFilter(opt.value)"
          >
            {{ opt.title }}
          </v-chip>
        </div>

        <!-- Loading -->
        <div v-if="recvPending" class="d-flex justify-center py-12">
          <v-progress-circular indeterminate color="primary" size="48" />
        </div>

        <v-alert v-else-if="recvError" type="error" variant="tonal" class="mb-4">
          Failed to load received interests.
        </v-alert>

        <template v-else-if="recvItems.length">
          <v-row>
            <v-col
              v-for="item in recvItems"
              :key="item.shortlist_id"
              cols="12"
              sm="6"
              md="4"
              lg="3"
            >
              <v-card rounded="xl" class="h-100">
                <!-- Photo -->
                <div
                  style="height:170px;overflow:hidden;position:relative;"
                  class="rounded-t-xl cursor-pointer"
                  @click="goToProfile(item.profile.id)"
                >
                  <v-img
                    v-if="recvPhotoUrls[item.profile.id]"
                    :src="recvPhotoUrls[item.profile.id]"
                    height="170"
                    cover
                    position="top center"
                    class="rounded-t-xl"
                  />
                  <div
                    v-else
                    class="d-flex align-center justify-center bg-grey-lighten-3 rounded-t-xl"
                    style="height:170px"
                  >
                    <v-icon size="72" color="grey-lighten-1">mdi-account-circle</v-icon>
                  </div>

                  <!-- Status chip for already-responded -->
                  <v-chip
                    v-if="item.status !== 'shortlisted'"
                    :color="statusColor(item.status)"
                    size="x-small"
                    label
                    style="position:absolute;top:8px;right:8px;z-index:1"
                  >
                    {{ fmtLabel(item.status) }}
                  </v-chip>

                  <!-- Pending badge -->
                  <v-chip
                    v-else
                    color="pink"
                    size="x-small"
                    label
                    style="position:absolute;top:8px;right:8px;z-index:1"
                  >
                    New Request
                  </v-chip>
                </div>

                <v-card-text class="pa-3 cursor-pointer" @click="goToProfile(item.profile.id)">
                  <p class="text-subtitle-2 font-weight-bold mb-0 text-truncate">
                    {{ item.profile.full_name || genderLabel(item.profile.gender) }}
                  </p>
                  <p class="text-caption text-medium-emphasis mb-1">
                    {{ ageLine(item.profile) }}
                  </p>
                  <div v-if="item.profile.city || item.profile.state" class="d-flex align-center gap-1">
                    <v-icon size="12" color="medium-emphasis">mdi-map-marker-outline</v-icon>
                    <span class="text-caption text-medium-emphasis text-truncate">
                      {{ [item.profile.city, item.profile.state].filter(Boolean).join(', ') }}
                    </span>
                  </div>
                  <div v-if="item.profile.profession" class="d-flex align-center gap-1 mt-1">
                    <v-icon size="12" color="medium-emphasis">mdi-briefcase-outline</v-icon>
                    <span class="text-caption text-medium-emphasis text-truncate">
                      {{ item.profile.profession }}
                    </span>
                  </div>
                  <p v-if="item.note" class="text-caption text-medium-emphasis mt-1 mb-0 text-truncate">
                    <v-icon size="12">mdi-note-text-outline</v-icon> "{{ item.note }}"
                  </p>
                  <p class="text-caption text-disabled mt-1 mb-0">
                    Received {{ fmtDate(item.created_at) }}
                  </p>
                </v-card-text>

                <!-- Accept / Reject (pending only) -->
                <v-card-actions v-if="item.status === 'shortlisted'" class="pt-0 px-3 pb-3 gap-2">
                  <v-btn
                    size="small"
                    color="success"
                    variant="flat"
                    flex
                    class="flex-grow-1"
                    :loading="responding[item.shortlist_id] === 'accepted'"
                    @click="respond(item.shortlist_id, 'accepted')"
                  >
                    <v-icon start size="16">mdi-check</v-icon>
                    Accept
                  </v-btn>
                  <v-btn
                    size="small"
                    color="error"
                    variant="tonal"
                    class="flex-grow-1"
                    :loading="responding[item.shortlist_id] === 'rejected'"
                    @click="respond(item.shortlist_id, 'rejected')"
                  >
                    <v-icon start size="16">mdi-close</v-icon>
                    Reject
                  </v-btn>
                </v-card-actions>
              </v-card>
            </v-col>
          </v-row>

          <div class="d-flex justify-center mt-6">
            <v-pagination v-model="recvPage" :length="recvPages" :total-visible="5" color="primary" />
          </div>
        </template>

        <div v-else class="text-center py-12 text-medium-emphasis">
          <v-icon size="64" class="mb-4">mdi-heart-flash</v-icon>
          <p class="text-h6">No interests received yet</p>
          <p class="text-body-2">When someone shortlists you, their request will appear here.</p>
        </div>
      </v-window-item>
    </v-window>

    <!-- Snackbar -->
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
import type { InterestEntry, Profile } from '@/types'

const router = useRouter()
const auth = useAuthStore()
const shortlistStore = useShortlistStore()
const qc = useQueryClient()

const tab = ref<'sent' | 'received'>('sent')

// ── Snackbar ────────────────────────────────────────────────────────────────
const snackbar = ref(false)
const snackText = ref('')
const snackColor = ref<'success' | 'error'>('success')

function notify(text: string, color: 'success' | 'error' = 'success') {
  snackText.value = text
  snackColor.value = color
  snackbar.value = true
}

// ── SENT tab ─────────────────────────────────────────────────────────────────
const sentPage = ref(1)
const sentPhotoUrls = reactive<Record<string, string>>({})
const withdrawing = reactive<Record<string, boolean>>({})

const { data: sentData, isPending: sentPending, isError: sentError } = useQuery({
  queryKey: computed(() => ['sent-interests', sentPage.value]),
  queryFn: () => shortlistApi.sentInterests(sentPage.value, 20),
})

const sentItems = computed<InterestEntry[]>(() => sentData.value?.items ?? [])
const sentPages = computed(() => sentData.value?.pages ?? 1)
const sentTotal = computed(() => sentData.value?.total ?? 0)

watch(sentItems, async (list) => {
  await fetchPhotoUrls(list.map((i) => i.profile), sentPhotoUrls)
}, { immediate: true })

async function withdraw(shortlistId: string, profileId: string) {
  withdrawing[shortlistId] = true
  try {
    await shortlistApi.delete(shortlistId)
    shortlistStore.removeFromMap(profileId)
    await Promise.all([
      qc.invalidateQueries({ queryKey: ['sent-interests'] }),
      qc.invalidateQueries({ queryKey: ['shortlisted-profiles'] }),
      qc.invalidateQueries({ queryKey: ['admin-shortlist-pairs'] }),
    ])
    notify('Interest withdrawn.')
  } catch {
    notify('Could not withdraw. Please try again.', 'error')
  } finally {
    delete withdrawing[shortlistId]
  }
}

// ── RECEIVED tab ──────────────────────────────────────────────────────────────
const recvPage = ref(1)
const recvPhotoUrls = reactive<Record<string, string>>({})
const receivedStatusFilter = ref<string | undefined>(undefined)
const responding = reactive<Record<string, 'accepted' | 'rejected'>>({})

const receivedFilters = [
  { title: 'All',         value: undefined },
  { title: 'Pending',     value: 'shortlisted' },
  { title: 'Accepted',    value: 'accepted' },
  { title: 'Rejected',    value: 'rejected' },
]

function applyReceivedFilter(value: string | undefined) {
  receivedStatusFilter.value = value
  recvPage.value = 1
}

const { data: recvData, isPending: recvPending, isError: recvError } = useQuery({
  queryKey: computed(() => ['received-interests', recvPage.value, receivedStatusFilter.value]),
  queryFn: () => shortlistApi.receivedInterests(recvPage.value, 20, receivedStatusFilter.value),
})

const recvItems = computed<InterestEntry[]>(() => recvData.value?.items ?? [])
const recvPages = computed(() => recvData.value?.pages ?? 1)
const pendingCount = computed(
  () => recvData.value?.items?.filter((i) => i.status === 'shortlisted').length ?? 0,
)

watch(recvItems, async (list) => {
  await fetchPhotoUrls(list.map((i) => i.profile), recvPhotoUrls)
}, { immediate: true })

async function respond(shortlistId: string, status: 'accepted' | 'rejected') {
  responding[shortlistId] = status
  try {
    await shortlistApi.respond(shortlistId, status)
    await Promise.all([
      qc.invalidateQueries({ queryKey: ['received-interests'] }),
      qc.invalidateQueries({ queryKey: ['admin-shortlist-pairs'] }),
    ])
    notify(status === 'accepted' ? 'Interest accepted!' : 'Interest rejected.')
  } catch {
    notify('Could not update. Please try again.', 'error')
  } finally {
    delete responding[shortlistId]
  }
}

// ── Shared helpers ────────────────────────────────────────────────────────────
async function fetchPhotoUrls(
  profiles: Profile[],
  urlMap: Record<string, string>,
) {
  const fetches = profiles
    .filter((p) => {
      if (!p.photo_keys?.length) return false
      const isOwn = auth.user?.id === p.user_id
      return auth.isAdmin || isOwn || p.photo_visible
    })
    .map(async (p) => {
      if (urlMap[p.id]) return
      try {
        const { url } = await filesApi.presignGet(p.photo_keys![0])
        urlMap[p.id] = url
      } catch { /* leave placeholder */ }
    })
  await Promise.allSettled(fetches)
}

function goToProfile(id: string) {
  router.push(`/profiles/${id}`)
}

function genderLabel(g: string | null): string {
  if (g === 'male') return 'Male'
  if (g === 'female') return 'Female'
  return 'Member'
}

function ageLine(p: Profile): string {
  const parts: string[] = []
  if (p.date_of_birth) {
    const d = new Date(p.date_of_birth)
    const t = new Date()
    let age = t.getFullYear() - d.getFullYear()
    if (t.getMonth() < d.getMonth() || (t.getMonth() === d.getMonth() && t.getDate() < d.getDate())) age--
    if (age >= 18 && age <= 80) parts.push(`${age} yrs`)
  }
  if (p.gender) parts.push(p.gender.charAt(0).toUpperCase() + p.gender.slice(1))
  return parts.join(' · ') || '—'
}

function fmtLabel(v: string): string {
  if (v === 'shortlisted') return 'Pending'
  return v.charAt(0).toUpperCase() + v.slice(1)
}

function fmtDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
}

function statusColor(s: string): string {
  if (s === 'accepted') return 'success'
  if (s === 'rejected') return 'error'
  return 'pink'
}

// Reset pagination when switching tabs
watch(tab, () => {
  sentPage.value = 1
  recvPage.value = 1
})

// Initialise shortlist store for the heart button state in Browse Profiles
shortlistStore.init()
</script>
