<template>
  <div>
    <!-- ── SUPER ADMIN DASHBOARD ──────────────────────────────────────────── -->
    <template v-if="auth.isSuperAdmin">
      <v-row class="mb-6">
        <v-col>
          <v-card color="primary" rounded="xl" class="pa-6">
            <div class="d-flex align-center flex-wrap ga-4">
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
            <v-card-text class="d-flex align-center ga-4 pa-5">
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
            <v-card-text class="d-flex align-center ga-4 pa-5">
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
            <v-card-text class="d-flex align-center ga-4 pa-5">
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
            <v-card-text class="d-flex align-center ga-4 pa-5">
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
            <v-card-text class="d-flex align-center ga-4 pa-5">
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
            <v-card-text class="d-flex align-center ga-4 pa-5">
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
            <div class="d-flex align-center flex-wrap ga-4">
              <v-icon size="48" class="opacity-75">mdi-account-circle</v-icon>
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
            <v-card-text class="d-flex align-center ga-4 pa-5">
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
            <v-card-text class="d-flex align-center ga-4 pa-5">
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
            <v-card-text class="d-flex align-center ga-4 pa-5">
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
            <v-card-text class="d-flex align-center ga-4 pa-5">
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
            <v-card-text class="d-flex align-center ga-4 pa-5">
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
                <template #item.profile_status="{ item }">
                  <v-chip
                    v-if="profileMap[item.id]"
                    :color="profileMap[item.id].status === 'active' ? 'success' : profileMap[item.id].status === 'suspended' ? 'error' : profileMap[item.id].status === 'matched' ? 'pink' : 'warning'"
                    size="small"
                  >
                    {{ profileMap[item.id].status === 'matched' ? 'Married' : profileMap[item.id].status }}
                  </v-chip>
                  <span v-else class="text-caption text-medium-emphasis">No profile</span>
                </template>
                <template #item.actions="{ item }">
                  <div v-if="profileMap[item.id]" class="d-flex align-center ga-1">
                    <v-switch
                      v-if="profileMap[item.id].status !== 'matched'"
                      :model-value="profileMap[item.id].status === 'active'"
                      color="success"
                      density="compact"
                      hide-details
                      :loading="togglingStatus[item.id] ?? false"
                      @update:model-value="(val: boolean | null) => toggleProfileStatus(item.id, val ?? false)"
                    />
                    <!-- Mark as Married and Delete Profile moved to individual profile view -->
                    <!--
                    <v-tooltip text="Mark as Married" location="top">
                      <template #activator="{ props: tp }">
                        <v-btn
                          v-if="profileMap[item.id].status !== 'matched'"
                          v-bind="tp"
                          icon="mdi-heart-multiple"
                          color="pink"
                          variant="text"
                          size="small"
                          :loading="togglingStatus[item.id] ?? false"
                          @click="markMarried(item.id)"
                        />
                      </template>
                    </v-tooltip>
                    <v-tooltip text="Delete Profile" location="top">
                      <template #activator="{ props: tp }">
                        <v-btn
                          v-bind="tp"
                          icon="mdi-delete"
                          color="error"
                          variant="text"
                          size="small"
                          :loading="togglingStatus[item.id] ?? false"
                          @click="confirmDeleteProfile(item.id)"
                        />
                      </template>
                    </v-tooltip>
                    -->
                  </div>
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
            <div class="d-flex align-center flex-wrap ga-4">
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
            <div class="d-flex align-center flex-wrap ga-3">
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
            <v-card-text class="d-flex align-center ga-4 pa-5">
              <v-icon color="green" size="36">mdi-check-circle</v-icon>
              <div>
                <p class="text-body-2 text-medium-emphasis mb-0">Profile Complete</p>
                <p class="text-h5 font-weight-bold mb-0">{{ profileCompletion }}%</p>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="12" sm="6" lg="3">
          <v-card rounded="xl" color="pink" variant="tonal" class="cursor-pointer" @click="router.push('/my-interests')">
            <v-card-text class="d-flex align-center ga-4 pa-5">
              <v-icon color="pink" size="36">mdi-heart-arrow</v-icon>
              <div>
                <p class="text-body-2 text-medium-emphasis mb-0">Interests Sent</p>
                <p class="text-h5 font-weight-bold mb-0">{{ memberStats.shortlisted }}</p>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="12" sm="6" lg="3">
          <v-card rounded="xl" color="deep-orange" variant="tonal" class="cursor-pointer" @click="router.push('/my-interests?tab=received')">
            <v-card-text class="d-flex align-center ga-4 pa-5">
              <v-icon color="deep-orange" size="36">mdi-heart-flash</v-icon>
              <div>
                <p class="text-body-2 text-medium-emphasis mb-0">Pending Requests</p>
                <p class="text-h5 font-weight-bold mb-0">{{ memberStats.pendingReceived }}</p>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="12" sm="6" lg="3">
          <v-card rounded="xl" color="blue" variant="tonal">
            <v-card-text class="d-flex align-center ga-4 pa-5">
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
            <v-card-text class="d-flex align-center ga-4 pa-5">
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
            <div class="d-flex flex-wrap ga-2 mt-3">
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
            <v-card-text class="d-flex align-center ga-4 pa-5">
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

    <!-- ── Mark Married Confirmation Dialog ────────────────────────────── -->
    <v-dialog v-model="marriedDialog" max-width="480" persistent>
      <v-card rounded="xl">
        <v-card-title class="d-flex align-center pa-4">
          <v-icon color="pink" class="mr-2">mdi-heart-multiple</v-icon>
          Mark as Married
        </v-card-title>
        <v-divider />
        <v-card-text class="pa-4">
          <p class="text-body-2 text-medium-emphasis mb-3">
            Are you sure you want to mark this member as married?
          </p>
          <v-alert type="info" variant="tonal" density="compact" class="mb-0">
            Their profile will be <strong>hidden</strong> from all other members immediately.
            You can still delete it later if needed.
          </v-alert>
        </v-card-text>
        <v-divider />
        <v-card-actions class="pa-4">
          <v-btn variant="text" @click="marriedDialog = false">Cancel</v-btn>
          <v-spacer />
          <v-btn
            color="pink"
            variant="elevated"
            prepend-icon="mdi-heart-multiple"
            :loading="togglingStatus[pendingActionUserId] ?? false"
            @click="executeMarkMarried"
          >
            Confirm
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- ── Delete Profile Confirmation Dialog ─────────────────────────── -->
    <v-dialog v-model="deleteDialog" max-width="480" persistent>
      <v-card rounded="xl">
        <v-card-title class="d-flex align-center pa-4">
          <v-icon color="error" class="mr-2">mdi-delete-alert</v-icon>
          Delete Profile
        </v-card-title>
        <v-divider />
        <v-card-text class="pa-4">
          <p class="text-body-2 text-medium-emphasis mb-3">
            Are you sure you want to permanently delete this profile?
          </p>
          <v-alert type="error" variant="tonal" density="compact" class="mb-0">
            This action <strong>cannot be undone</strong>. All profile data, photos,
            shortlists, and partner preferences will be permanently removed.
          </v-alert>
        </v-card-text>
        <v-divider />
        <v-card-actions class="pa-4">
          <v-btn variant="text" @click="deleteDialog = false">Cancel</v-btn>
          <v-spacer />
          <v-btn
            color="error"
            variant="elevated"
            prepend-icon="mdi-delete"
            :loading="togglingStatus[pendingActionUserId] ?? false"
            @click="executeDeleteProfile"
          >
            Delete Permanently
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { profilesApi } from '@/api/profiles'
import { shortlistApi } from '@/api/shortlist'
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

// Server-side accurate counts (avoid frontend pagination truncation)
const adminStatCounts = ref({ active: 0, draft: 0, male: 0, female: 0 })

const adminStats = computed(() => ({
  totalMembers: members.value.length,
  activeProfiles: adminStatCounts.value.active,
  draftProfiles: adminStatCounts.value.draft,
  maleCount: adminStatCounts.value.male,
  femaleCount: adminStatCounts.value.female,
}))

const memberHeaders = [
  { title: 'Name', key: 'full_name', sortable: true },
  { title: 'Email', key: 'email' },
  { title: 'Phone', key: 'phone' },
  { title: 'Verified', key: 'is_verified', sortable: true },
  { title: 'Account', key: 'is_active', sortable: true },
  { title: 'Profile', key: 'profile_status', sortable: false },
  { title: 'Active', key: 'actions', sortable: false },
  { title: 'Joined', key: 'created_at', sortable: true },
]

const adminActions = [
  { title: 'Browse Profiles', subtitle: 'View all member profiles', icon: 'mdi-account-group', color: 'primary', to: '/profiles' },
  { title: 'Shortlist Manager', subtitle: 'Review shortlisted pairs', icon: 'mdi-heart-multiple', color: 'pink', to: '/admin/shortlists' },
]

async function loadMembers() {
  loadingMembers.value = true
  try {
    const res = await client.get('/users/members', { params: { page: 1, size: 200 } }).then((r) => r.data)
    members.value = res.items ?? res
    // Load profiles to get each member's profile status
    await loadProfileMap()
  } catch {
    members.value = []
  } finally {
    loadingMembers.value = false
  }
}

// Map user_id → profile for showing profile status in the members table
const profileMap = ref<Record<string, { id: string; status: string }>>({});
const togglingStatus = ref<Record<string, boolean>>({});
const marriedDialog = ref(false)
const deleteDialog = ref(false)
const pendingActionUserId = ref('')

async function loadProfileMap() {
  try {
    const map: Record<string, { id: string; status: string }> = {}
    let page = 1
    const size = 100
    let pages = 1
    do {
      const res = await profilesApi.list({ page, size })
      for (const p of res.items) {
        map[p.user_id] = { id: p.id, status: p.status }
      }
      pages = res.pages
      page++
    } while (page <= pages)
    profileMap.value = map
  } catch {
    profileMap.value = {}
  }
}

async function toggleProfileStatus(userId: string, activate: boolean) {
  const entry = profileMap.value[userId]
  if (!entry) return
  togglingStatus.value[userId] = true
  try {
    const updated = await profilesApi.setStatus(entry.id, activate ? 'active' : 'suspended')
    profileMap.value[userId] = { id: entry.id, status: updated.status }
  } catch {
    // revert silently on failure
  } finally {
    togglingStatus.value[userId] = false
  }
}

async function markMarried(userId: string) {
  const entry = profileMap.value[userId]
  if (!entry) return
  pendingActionUserId.value = userId
  marriedDialog.value = true
}

async function executeMarkMarried() {
  const userId = pendingActionUserId.value
  const entry = profileMap.value[userId]
  if (!entry) return
  togglingStatus.value[userId] = true
  try {
    const updated = await profilesApi.setStatus(entry.id, 'matched')
    profileMap.value[userId] = { id: entry.id, status: updated.status }
  } catch {
    // ignore
  } finally {
    togglingStatus.value[userId] = false
    marriedDialog.value = false
  }
}

async function confirmDeleteProfile(userId: string) {
  const entry = profileMap.value[userId]
  if (!entry) return
  pendingActionUserId.value = userId
  deleteDialog.value = true
}

async function executeDeleteProfile() {
  const userId = pendingActionUserId.value
  const entry = profileMap.value[userId]
  if (!entry) return
  togglingStatus.value[userId] = true
  try {
    await profilesApi.delete(entry.id)
    delete profileMap.value[userId]
    await loadAdminProfiles()
  } catch {
    // ignore
  } finally {
    togglingStatus.value[userId] = false
    deleteDialog.value = false
  }
}

async function loadAdminProfiles() {
  try {
    const [totalRes, activeRes, maleRes, femaleRes] = await Promise.all([
      profilesApi.list({ size: 1 }),
      profilesApi.list({ status: 'active', size: 1 }),
      profilesApi.list({ gender: 'male', size: 1 }),
      profilesApi.list({ gender: 'female', size: 1 }),
    ])
    adminStatCounts.value = {
      active: activeRes.total ?? 0,
      draft: (totalRes.total ?? 0) - (activeRes.total ?? 0),
      male: maleRes.total ?? 0,
      female: femaleRes.total ?? 0,
    }
  } catch {
    adminStatCounts.value = { active: 0, draft: 0, male: 0, female: 0 }
  }
}

// ────────────────────────────────────────────────────────────────────────────
// MEMBER state
// ────────────────────────────────────────────────────────────────────────────
const myProfile = ref<Profile | null>(null)
const memberStats = ref({ shortlisted: '—', pendingReceived: '—', totalProfiles: '—' })

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
  { title: 'My Interests', subtitle: 'Sent & received interest requests', icon: 'mdi-heart-multiple-outline', color: 'pink', to: '/my-interests' },
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
    const [profilesRes, sentRes, receivedRes] = await Promise.all([
      profilesApi.list({ size: 1 }),
      shortlistApi.sentInterests(1, 1),
      shortlistApi.receivedInterests(1, 1, 'shortlisted'),
    ])
    memberStats.value.totalProfiles = String(profilesRes.total)
    memberStats.value.shortlisted = String(sentRes.total)
    memberStats.value.pendingReceived = String(receivedRes.total)
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
