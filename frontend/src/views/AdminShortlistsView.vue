<template>
  <div>
    <h1 class="text-h5 font-weight-bold mb-2">Shortlist Manager</h1>
    <p class="text-body-2 text-medium-emphasis mb-6">
      Review all shortlisted pairs in your centre.
    </p>

    <!-- Status filter -->
    <v-card rounded="xl" class="mb-6">
      <v-card-text>
        <v-row dense align="center">
          <v-col cols="12" sm="4" md="3">
            <v-select
              v-model="statusFilter"
              label="Filter by Status"
              :items="statusOptions"
              variant="outlined"
              density="compact"
              clearable
              hide-details
            />
          </v-col>
          <v-col cols="auto">
            <v-chip-group v-model="statusFilter" selected-class="text-primary" mandatory>
              <v-chip v-for="s in statusOptions" :key="s.value" :value="s.value" size="small" filter>
                {{ s.title }}
              </v-chip>
            </v-chip-group>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- Table -->
    <v-card rounded="xl">
      <v-data-table-server
        v-model:page="page"
        :items="pairs"
        :items-length="total"
        :items-per-page="pageSize"
        :headers="headers"
        :loading="isPending"
        :items-per-page-options="[{ value: 20, title: '20' }]"
        hover
      >
        <!-- From profile -->
        <template #item.from_profile="{ item }">
          <div class="py-2">
            <p class="font-weight-medium mb-0">{{ item.from_profile.full_name || '—' }}</p>
            <p class="text-caption text-medium-emphasis mb-0">
              {{ ageLine(item.from_profile) }}
              <span v-if="item.from_profile.city"> · {{ item.from_profile.city }}</span>
            </p>
          </div>
        </template>

        <!-- Arrow -->
        <template #item.arrow>
          <v-icon color="pink">mdi-arrow-right-bold</v-icon>
        </template>

        <!-- To profile -->
        <template #item.to_profile="{ item }">
          <div class="py-2">
            <p class="font-weight-medium mb-0">{{ item.to_profile.full_name || '—' }}</p>
            <p class="text-caption text-medium-emphasis mb-0">
              {{ ageLine(item.to_profile) }}
              <span v-if="item.to_profile.city"> · {{ item.to_profile.city }}</span>
            </p>
          </div>
        </template>

        <!-- Status chip -->
        <template #item.status="{ item }">
          <v-chip
            :color="statusColor(item.status)"
            size="small"
            label
            variant="tonal"
          >
            {{ fmtLabel(item.status) }}
          </v-chip>
        </template>

        <!-- Note -->
        <template #item.note="{ item }">
          <span class="text-caption text-medium-emphasis">{{ item.note || '—' }}</span>
        </template>

        <!-- Date -->
        <template #item.created_at="{ item }">
          <span class="text-caption">{{ fmtDate(item.created_at) }}</span>
        </template>

        <!-- Empty state -->
        <template #no-data>
          <div class="text-center py-8 text-medium-emphasis">
            <v-icon size="48" class="mb-2">mdi-heart-off-outline</v-icon>
            <p class="text-body-2">No shortlist pairs found{{ statusFilter ? ' for this status' : '' }}.</p>
          </div>
        </template>
      </v-data-table-server>
    </v-card>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, watch } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import client from '@/api/client'
import type { ShortlistStatus } from '@/types'

// ── Types ─────────────────────────────────────────────────────────────────────
interface ProfileSummary {
  id: string
  full_name: string | null
  gender: string | null
  date_of_birth: string | null
  city: string | null
  state: string | null
}

interface ShortlistPair {
  id: string
  from_profile: ProfileSummary
  to_profile: ProfileSummary
  status: ShortlistStatus
  note: string | null
  created_at: string
  updated_at: string
}

interface PairList {
  items: ShortlistPair[]
  total: number
  page: number
  size: number
  pages: number
}

// ── State ─────────────────────────────────────────────────────────────────────
const page = ref(1)
const pageSize = 20
const statusFilter = ref<string | undefined>(undefined)

watch(statusFilter, () => { page.value = 1 })

const statusOptions = [
  { title: 'Shortlisted', value: 'shortlisted' },
  { title: 'Accepted',    value: 'accepted' },
  { title: 'Rejected',    value: 'rejected' },
]

const headers = [
  { title: 'From (Sender)',    key: 'from_profile', sortable: false },
  { title: '',                 key: 'arrow',        sortable: false, width: 40 },
  { title: 'To (Recipient)',   key: 'to_profile',   sortable: false },
  { title: 'Status',           key: 'status',       sortable: false },
  { title: 'Note',             key: 'note',         sortable: false },
  { title: 'Date',             key: 'created_at',   sortable: false },
]

// ── Query ──────────────────────────────────────────────────────────────────────
const { data, isPending } = useQuery({
  queryKey: computed(() => ['admin-shortlist-pairs', page.value, statusFilter.value]),
  queryFn: (): Promise<PairList> =>
    client.get('/shortlists/admin/pairs', {
      params: {
        page: page.value,
        size: pageSize,
        ...(statusFilter.value ? { status: statusFilter.value } : {}),
      },
    }).then((r) => r.data),
})

const pairs = computed<ShortlistPair[]>(() => data.value?.items ?? [])
const total = computed(() => data.value?.total ?? 0)

// ── Helpers ────────────────────────────────────────────────────────────────────
function fmtLabel(v: string): string {
  return v.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

function fmtDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
}

function ageLine(p: ProfileSummary): string {
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

function statusColor(s: string): string {
  if (s === 'accepted') return 'success'
  if (s === 'rejected') return 'error'
  return 'pink'
}
</script>
