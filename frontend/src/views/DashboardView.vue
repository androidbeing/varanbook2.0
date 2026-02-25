<template>
  <div>
    <!-- ── SUPER ADMIN DASHBOARD ──────────────────────────────────────────── -->
    <template v-if="auth.isSuperAdmin">
      <v-row class="mb-6">
        <v-col>
          <v-card color="primary" rounded="xl" class="pa-6">
            <div class="d-flex align-center flex-wrap gap-4">
              <v-icon size="48" class="opacity-75">mdi-shield-crown</v-icon>
              <div>
                <h1 class="text-h5 font-weight-bold">Super Admin Console</h1>
                <p class="text-body-2 opacity-80 mb-0">
                  Manage matrimonial centres and platform-wide settings.
                </p>
              </div>
            </div>
          </v-card>
        </v-col>
      </v-row>

      <!-- Stat Cards -->
      <v-row class="mb-4">
        <v-col cols="12" sm="6" lg="3">
          <v-card rounded="xl" color="blue" variant="tonal">
            <v-card-text class="d-flex align-center gap-4 pa-5">
              <v-icon color="blue" size="36">mdi-office-building-cog</v-icon>
              <div>
                <p class="text-body-2 text-medium-emphasis mb-0">Total Tenants</p>
                <p class="text-h5 font-weight-bold mb-0">{{ superStats.total }}</p>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="12" sm="6" lg="3">
          <v-card rounded="xl" color="green" variant="tonal">
            <v-card-text class="d-flex align-center gap-4 pa-5">
              <v-icon color="green" size="36">mdi-check-circle</v-icon>
              <div>
                <p class="text-body-2 text-medium-emphasis mb-0">Active</p>
                <p class="text-h5 font-weight-bold mb-0">{{ superStats.active }}</p>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="12" sm="6" lg="3">
          <v-card rounded="xl" color="red" variant="tonal">
            <v-card-text class="d-flex align-center gap-4 pa-5">
              <v-icon color="red" size="36">mdi-close-circle</v-icon>
              <div>
                <p class="text-body-2 text-medium-emphasis mb-0">Inactive</p>
                <p class="text-h5 font-weight-bold mb-0">{{ superStats.inactive }}</p>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="12" sm="6" lg="3">
          <v-card rounded="xl" color="purple" variant="tonal">
            <v-card-text class="d-flex align-center gap-4 pa-5">
              <v-icon color="purple" size="36">mdi-account-group</v-icon>
              <div>
                <p class="text-body-2 text-medium-emphasis mb-0">Total Admins</p>
                <p class="text-h5 font-weight-bold mb-0">{{ superStats.admins }}</p>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- Quick Actions -->
      <v-row class="mb-6">
        <v-col cols="12">
          <h2 class="text-h6 font-weight-semibold mb-3">Quick Actions</h2>
        </v-col>
        <v-col cols="12" sm="6" md="4">
          <v-card rounded="xl" hover class="cursor-pointer" @click="router.push('/admin/tenants')">
            <v-card-text class="d-flex align-center gap-4 pa-5">
              <v-avatar color="blue" variant="tonal" size="44">
                <v-icon>mdi-office-building-plus</v-icon>
              </v-avatar>
              <div>
                <p class="font-weight-semibold mb-0">Add New Tenant</p>
                <p class="text-body-2 text-medium-emphasis mb-0">Onboard a matrimonial centre</p>
              </div>
              <v-spacer />
              <v-icon color="medium-emphasis">mdi-chevron-right</v-icon>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="12" sm="6" md="4">
          <v-card rounded="xl" hover class="cursor-pointer" @click="router.push('/admin/tenants')">
            <v-card-text class="d-flex align-center gap-4 pa-5">
              <v-avatar color="purple" variant="tonal" size="44">
                <v-icon>mdi-office-building-cog</v-icon>
              </v-avatar>
              <div>
                <p class="font-weight-semibold mb-0">Manage Tenants</p>
                <p class="text-body-2 text-medium-emphasis mb-0">View and edit all centres</p>
              </div>
              <v-spacer />
              <v-icon color="medium-emphasis">mdi-chevron-right</v-icon>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- Tenant List -->
      <v-row>
        <v-col cols="12">
          <v-card rounded="xl">
            <v-card-title class="pa-5 pb-0 d-flex align-center">
              <span>Registered Tenants</span>
              <v-spacer />
              <v-btn
                variant="tonal"
                color="primary"
                size="small"
                prepend-icon="mdi-reload"
                :loading="loadingTenants"
                @click="loadTenants"
              >
                Refresh
              </v-btn>
            </v-card-title>
            <v-card-text class="pa-0">
              <v-data-table
                :headers="tenantHeaders"
                :items="tenants"
                :loading="loadingTenants"
                items-per-page="10"
                class="rounded-xl"
              >
                <template #item.is_active="{ item }">
                  <v-chip :color="item.is_active ? 'success' : 'error'" size="small">
                    {{ item.is_active ? 'Active' : 'Inactive' }}
                  </v-chip>
                </template>
                <template #item.plan="{ item }">
                  <v-chip color="blue" size="small" variant="tonal">{{ item.plan }}</v-chip>
                </template>
                <template #item.max_users="{ item }">
                  {{ item.max_users }} users / {{ item.max_admins }} admins
                </template>
              </v-data-table>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </template>

    <!-- ── ADMIN DASHBOARD ────────────────────────────────────────────────── -->
    <template v-else-if="auth.isAdmin">
      <v-row class="mb-6">
        <v-col>
          <v-card color="primary" rounded="xl" class="pa-6">
            <div class="d-flex align-center flex-wrap gap-4">
              <v-icon size="48" class="opacity-75">mdi-account-tie</v-icon>
              <div>
                <h1 class="text-h5 font-weight-bold">
                  Welcome, {{ firstName }}!
                </h1>
                <p class="text-body-2 opacity-80 mb-0">
                  Manage your matrimonial centre members and profiles.
                </p>
              </div>
              <v-spacer />
              <v-btn
                color="white"
                variant="elevated"
                prepend-icon="mdi-account-multiple"
                @click="router.push('/profiles')"
              >
                Browse Profiles
              </v-btn>
            </div>
          </v-card>
        </v-col>
      </v-row>

      <!-- Stat Cards -->
      <v-row class="mb-4">
        <v-col cols="12" sm="6" lg="3">
          <v-card rounded="xl" color="blue" variant="tonal">
            <v-card-text class="d-flex align-center gap-4 pa-5">
              <v-icon color="blue" size="36">mdi-account-group</v-icon>
              <div>
                <p class="text-body-2 text-medium-emphasis mb-0">Total Members</p>
                <p class="text-h5 font-weight-bold mb-0">{{ adminStats.totalMembers }}</p>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="12" sm="6" lg="3">
          <v-card rounded="xl" color="green" variant="tonal">
            <v-card-text class="d-flex align-center gap-4 pa-5">
              <v-icon color="green" size="36">mdi-account-check</v-icon>
              <div>
                <p class="text-body-2 text-medium-emphasis mb-0">Active Profiles</p>
                <p class="text-h5 font-weight-bold mb-0">{{ adminStats.activeProfiles }}</p>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="12" sm="6" lg="3">
          <v-card rounded="xl" color="orange" variant="tonal">
            <v-card-text class="d-flex align-center gap-4 pa-5">
              <v-icon color="orange" size="36">mdi-account-clock</v-icon>
              <div>
                <p class="text-body-2 text-medium-emphasis mb-0">Draft/Pending</p>
                <p class="text-h5 font-weight-bold mb-0">{{ adminStats.draftProfiles }}</p>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="12" sm="6" lg="3">
          <v-card rounded="xl" color="purple" variant="tonal">
            <v-card-text class="d-flex align-center gap-4 pa-5">
              <v-icon color="purple" size="36">mdi-gender-male-female</v-icon>
              <div>
                <p class="text-body-2 text-medium-emphasis mb-0">Male / Female</p>
                <p class="text-h5 font-weight-bold mb-0">{{ adminStats.maleCount }} / {{ adminStats.femaleCount }}</p>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- Quick Actions -->
      <v-row class="mb-6">
        <v-col cols="12">
          <h2 class="text-h6 font-weight-semibold mb-3">Quick Actions</h2>
        </v-col>
        <v-col v-for="action in adminActions" :key="action.title" cols="12" sm="6" md="4">
          <v-card rounded="xl" hover class="cursor-pointer" @click="router.push(action.to)">
            <v-card-text class="d-flex align-center gap-4 pa-5">
              <v-avatar :color="action.color" variant="tonal" size="44">
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

      <!-- Member List -->
      <v-row>
        <v-col cols="12">
          <v-card rounded="xl">
            <v-card-title class="pa-5 pb-0 d-flex align-center">
              <span>Members</span>
              <v-spacer />
              <v-btn
                variant="tonal"
                color="primary"
                size="small"
                prepend-icon="mdi-reload"
                :loading="loadingMembers"
                @click="loadMembers"
              >
                Refresh
              </v-btn>
            </v-card-title>
            <v-card-text class="pa-0">
              <v-data-table
                :headers="memberHeaders"
                :items="members"
                :loading="loadingMembers"
                items-per-page="10"
                class="rounded-xl"
              >
                <template #item.is_active="{ item }">
                  <v-chip :color="item.is_active ? 'success' : 'error'" size="small">
                    {{ item.is_active ? 'Active' : 'Inactive' }}
                  </v-chip>
                </template>
                <template #item.is_verified="{ item }">
                  <v-icon :color="item.is_verified ? 'success' : 'grey'" size="20">
                    {{ item.is_verified ? 'mdi-check-circle' : 'mdi-clock-outline' }}
                  </v-icon>
                </template>
                <template #item.created_at="{ item }">
                  {{ new Date(item.created_at).toLocaleDateString('en-IN') }}
                </template>
              </v-data-table>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </template>

    <!-- ── MEMBER DASHBOARD ───────────────────────────────────────────────── -->
    <template v-else>
      <v-row class="mb-6">
        <v-col>
          <v-card color="primary" rounded="xl" class="pa-6">
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

      <!-- Profile completion alert -->
      <v-row v-if="profileCompletion < 60" class="mb-4">
        <v-col>
          <v-alert type="warning" variant="tonal" rounded="xl" border="start">
            <div class="d-flex align-center flex-wrap gap-3">
              <div>
                <strong>Your profile is {{ profileCompletion }}% complete.</strong>
                Complete your profile to get better matches!
              </div>
              <v-btn size="small" color="warning" variant="elevated" @click="router.push('/my-profile')">
                Complete Profile
              </v-btn>
            </div>
          </v-alert>
        </v-col>
      </v-row>

      <!-- Stat Cards -->
      <v-row class="mb-4">
        <v-col cols="12" sm="6" lg="3">
          <v-card rounded="xl" color="green" variant="tonal">
            <v-card-text class="d-flex align-center gap-4 pa-5">
              <v-icon color="green" size="36">mdi-check-circle</v-icon>
              <div>
                <p class="text-body-2 text-medium-emphasis mb-0">Profile Complete</p>
                <p class="text-h5 font-weight-bold mb-0">{{ profileCompletion }}%</p>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="12" sm="6" lg="3">
          <v-card rounded="xl" color="pink" variant="tonal">
            <v-card-text class="d-flex align-center gap-4 pa-5">
              <v-icon color="pink" size="36">mdi-heart</v-icon>
              <div>
                <p class="text-body-2 text-medium-emphasis mb-0">Shortlisted</p>
                <p class="text-h5 font-weight-bold mb-0">{{ memberStats.shortlisted }}</p>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="12" sm="6" lg="3">
          <v-card rounded="xl" color="blue" variant="tonal">
            <v-card-text class="d-flex align-center gap-4 pa-5">
              <v-icon color="blue" size="36">mdi-account-multiple-check</v-icon>
              <div>
                <p class="text-body-2 text-medium-emphasis mb-0">Total Profiles</p>
                <p class="text-h5 font-weight-bold mb-0">{{ memberStats.totalProfiles }}</p>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="12" sm="6" lg="3">
          <v-card rounded="xl" :color="myProfile?.status === 'active' ? 'green' : 'orange'" variant="tonal">
            <v-card-text class="d-flex align-center gap-4 pa-5">
              <v-icon :color="myProfile?.status === 'active' ? 'green' : 'orange'" size="36">
                mdi-account-circle
              </v-icon>
              <div>
                <p class="text-body-2 text-medium-emphasis mb-0">Profile Status</p>
                <p class="text-h5 font-weight-bold mb-0 text-capitalize">
                  {{ myProfile?.status ?? '—' }}
                </p>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- Profile completion bar -->
      <v-row class="mb-4">
        <v-col>
          <v-card rounded="xl" class="pa-5">
            <div class="d-flex align-center mb-2">
              <span class="font-weight-semibold">Biodata Completion</span>
              <v-spacer />
              <span class="text-body-2 text-medium-emphasis">{{ profileCompletion }}%</span>
            </div>
            <v-progress-linear
              :model-value="profileCompletion"
              color="primary"
              height="10"
              rounded
              bg-color="grey-lighten-3"
            />
            <div class="d-flex flex-wrap gap-2 mt-3">
              <v-chip
                v-for="sec in profileSections"
                :key="sec.label"
                :color="sec.done ? 'success' : 'grey'"
                size="small"
                variant="tonal"
              >
                <v-icon start size="12" :icon="sec.done ? 'mdi-check' : 'mdi-circle-outline'" />
                {{ sec.label }}
              </v-chip>
            </div>
          </v-card>
        </v-col>
      </v-row>

      <!-- Quick Actions -->
      <v-row>
        <v-col cols="12">
          <h2 class="text-h6 font-weight-semibold mb-3">Quick Actions</h2>
        </v-col>
        <v-col v-for="action in memberActions" :key="action.title" cols="12" sm="6" md="4">
          <v-card rounded="xl" hover class="cursor-pointer" @click="router.push(action.to)">
            <v-card-text class="d-flex align-center gap-4 pa-5">
              <v-avatar :color="action.color" variant="tonal" size="44">
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
    </template>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { profilesApi } from '@/api/profiles'
import client from '@/api/client'
import type { Profile } from '@/types'

const router = useRouter()
const auth = useAuthStore()

const firstName = computed(() => auth.user?.full_name?.split(' ')[0] ?? 'User')

// ────────────────────────────────────────────────────────────────────────────
// SUPER ADMIN state
// ────────────────────────────────────────────────────────────────────────────
const tenants = ref<any[]>([])
const loadingTenants = ref(false)

const superStats = computed(() => ({
  total: tenants.value.length,
  active: tenants.value.filter((t) => t.is_active).length,
  inactive: tenants.value.filter((t) => !t.is_active).length,
  admins: tenants.value.reduce((sum, t) => sum + (t.max_admins ?? 0), 0),
}))

const tenantHeaders = [
  { title: 'Name', key: 'name', sortable: true },
  { title: 'Slug', key: 'slug' },
  { title: 'Contact Email', key: 'contact_email' },
  { title: 'Plan', key: 'plan' },
  { title: 'Capacity', key: 'max_users', sortable: false },
  { title: 'Status', key: 'is_active', sortable: true },
]

async function loadTenants() {
  loadingTenants.value = true
  try {
    const res = await client.get('/admin/tenants/', { params: { page: 1, size: 100 } }).then((r) => r.data)
    tenants.value = res.items ?? res
  } catch {
    tenants.value = []
  } finally {
    loadingTenants.value = false
  }
}

// ────────────────────────────────────────────────────────────────────────────
// ADMIN state
// ────────────────────────────────────────────────────────────────────────────
const members = ref<any[]>([])
const loadingMembers = ref(false)
const allProfiles = ref<Profile[]>([])

const adminStats = computed(() => {
  const active = allProfiles.value.filter((p) => p.status === 'active').length
  const draft = allProfiles.value.filter((p) => p.status !== 'active').length
  const male = allProfiles.value.filter((p) => p.gender === 'male').length
  const female = allProfiles.value.filter((p) => p.gender === 'female').length
  return {
    totalMembers: members.value.length,
    activeProfiles: active,
    draftProfiles: draft,
    maleCount: male,
    femaleCount: female,
  }
})

const memberHeaders = [
  { title: 'Name', key: 'full_name', sortable: true },
  { title: 'Email', key: 'email' },
  { title: 'Phone', key: 'phone' },
  { title: 'Verified', key: 'is_verified', sortable: true },
  { title: 'Status', key: 'is_active', sortable: true },
  { title: 'Joined', key: 'created_at', sortable: true },
]

const adminActions = [
  { title: 'Browse Profiles', subtitle: 'View all member profiles', icon: 'mdi-account-group', color: 'primary', to: '/profiles' },
  { title: 'Shortlist Manager', subtitle: 'Review shortlisted pairs', icon: 'mdi-heart-multiple', color: 'pink', to: '/profiles' },
]

async function loadMembers() {
  loadingMembers.value = true
  try {
    const res = await client.get('/users/members', { params: { page: 1, size: 200 } }).then((r) => r.data)
    members.value = res.items ?? res
  } catch {
    members.value = []
  } finally {
    loadingMembers.value = false
  }
}

async function loadAdminProfiles() {
  try {
    const res = await profilesApi.list({ size: 200 })
    allProfiles.value = res.items ?? []
  } catch {
    allProfiles.value = []
  }
}

// ────────────────────────────────────────────────────────────────────────────
// MEMBER state
// ────────────────────────────────────────────────────────────────────────────
const myProfile = ref<Profile | null>(null)
const memberStats = ref({ shortlisted: '—', totalProfiles: '—' })

const profileSections = computed(() => {
  const p = myProfile.value
  if (!p) return []
  return [
    { label: 'Personal', done: !!(p.gender && p.date_of_birth && p.religion && p.caste) },
    { label: 'Birth Details', done: !!(p.rashi && p.star) },
    { label: 'Professional', done: !!(p.qualification && p.profession) },
    { label: 'Family', done: !!(p.father_name && p.mother_name) },
    { label: 'Contact', done: !!(p.mobile && p.current_location) },
    { label: 'Photos', done: !!((p.photo_keys?.length ?? 0) > 0) },
  ]
})

const profileCompletion = computed(() => {
  if (!myProfile.value) return 0
  const done = profileSections.value.filter((s) => s.done).length
  return Math.round((done / profileSections.value.length) * 100)
})

const memberActions = [
  { title: 'Browse Profiles', subtitle: 'Find your match', icon: 'mdi-account-group', color: 'primary', to: '/profiles' },
  { title: 'Edit My Profile', subtitle: 'Keep your biodata updated', icon: 'mdi-account-edit', color: 'teal', to: '/my-profile' },
  { title: 'Partner Preferences', subtitle: 'Set your ideal match criteria', icon: 'mdi-heart-search', color: 'pink', to: '/my-profile' },
]

async function loadMyProfile() {
  try {
    myProfile.value = await profilesApi.mine()
  } catch {
    myProfile.value = null
  }
}

async function loadMemberBrowseCount() {
  try {
    const res = await profilesApi.list({ size: 1 })
    memberStats.value.totalProfiles = String(res.total)
  } catch {
    // ignore
  }
}

// ────────────────────────────────────────────────────────────────────────────
// Init
// ────────────────────────────────────────────────────────────────────────────
onMounted(async () => {
  if (auth.isSuperAdmin) {
    await loadTenants()
  } else if (auth.isAdmin) {
    await Promise.all([loadMembers(), loadAdminProfiles()])
  } else {
    await Promise.all([loadMyProfile(), loadMemberBrowseCount()])
  }
})
</script>
