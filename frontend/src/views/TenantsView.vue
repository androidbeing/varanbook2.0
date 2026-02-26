<template>
  <div>
    <!-- Header -->
    <v-row class="mb-6">
      <v-col>
        <v-card color="primary" rounded="xl" class="pa-6">
          <div class="d-flex align-center flex-wrap gap-4">
            <v-icon size="48" class="opacity-75">mdi-office-building-cog</v-icon>
            <div class="flex-grow-1">
              <h1 class="text-h5 font-weight-bold">Manage Tenants</h1>
              <p class="text-body-2 opacity-80 mb-0">
                View, edit and manage all matrimonial centre accounts.
              </p>
            </div>
            <v-btn
              color="white"
              variant="elevated"
              prepend-icon="mdi-office-building-plus"
              @click="router.push('/admin/tenants/new')"
            >
              New Tenant
            </v-btn>
          </div>
        </v-card>
      </v-col>
    </v-row>

    <!-- Filters -->
    <v-row class="mb-4" align="center">
      <v-col cols="12" sm="6" md="4">
        <v-text-field
          v-model="search"
          label="Search tenants…"
          prepend-inner-icon="mdi-magnify"
          clearable
          variant="outlined"
          density="compact"
          hide-details
        />
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-select
          v-model="filterActive"
          :items="activeOptions"
          label="Status"
          variant="outlined"
          density="compact"
          hide-details
          clearable
        />
      </v-col>
      <v-spacer />
      <v-col cols="auto">
        <v-btn
          variant="tonal"
          prepend-icon="mdi-reload"
          :loading="loading"
          @click="load"
        >
          Refresh
        </v-btn>
      </v-col>
    </v-row>

    <!-- Table -->
    <v-card rounded="xl">
      <v-data-table
        :headers="headers"
        :items="filteredTenants"
        :loading="loading"
        items-per-page="15"
        class="rounded-xl"
      >
        <!-- Status chip -->
        <template #item.is_active="{ item }">
          <v-chip :color="item.is_active ? 'success' : 'error'" size="small">
            {{ item.is_active ? 'Active' : 'Inactive' }}
          </v-chip>
        </template>

        <!-- Plan chip -->
        <template #item.plan="{ item }">
          <v-chip
            :color="planColor(item.plan)"
            size="small"
            variant="tonal"
            class="text-capitalize"
          >
            {{ item.plan }}
          </v-chip>
        </template>

        <!-- Limits -->
        <template #item.limits="{ item }">
          <span class="text-body-2 text-medium-emphasis">
            {{ item.max_users }} users / {{ item.max_admins }} admins
          </span>
        </template>

        <!-- Created -->
        <template #item.created_at="{ item }">
          <span class="text-body-2">{{ formatDate(item.created_at) }}</span>
        </template>

        <!-- Actions -->
        <template #item.actions="{ item }">
          <div class="d-flex gap-1">
            <v-tooltip text="Edit tenant">
              <template #activator="{ props }">
                <v-btn
                  v-bind="props"
                  icon="mdi-pencil"
                  size="small"
                  variant="text"
                  color="primary"
                  @click="openEdit(item)"
                />
              </template>
            </v-tooltip>
            <v-tooltip :text="item.is_active ? 'Deactivate' : 'Already inactive'">
              <template #activator="{ props }">
                <v-btn
                  v-bind="props"
                  icon="mdi-close-circle-outline"
                  size="small"
                  variant="text"
                  color="error"
                  :disabled="!item.is_active"
                  @click="confirmDeactivate(item)"
                />
              </template>
            </v-tooltip>
          </div>
        </template>
      </v-data-table>
    </v-card>

    <!-- Edit Dialog -->
    <v-dialog v-model="editDialog" max-width="600" persistent>
      <v-card rounded="xl" v-if="editTenant">
        <v-card-title class="pa-5 pb-0">
          <v-icon class="mr-2">mdi-pencil</v-icon>Edit Tenant
        </v-card-title>
        <v-card-text class="pa-5">
          <v-row dense>
            <v-col cols="12" sm="6">
              <v-text-field v-model="editForm.name" label="Centre Name" variant="outlined" density="compact" />
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field v-model="editForm.contact_email" label="Contact Email" variant="outlined" density="compact" />
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field v-model="editForm.contact_person" label="Contact Person" variant="outlined" density="compact" />
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field v-model="editForm.contact_number" label="Contact Number" variant="outlined" density="compact" placeholder="+919876543210" />
            </v-col>
            <v-col cols="12" sm="6">
              <v-select
                v-model="editForm.plan"
                :items="planOptions"
                label="Plan"
                variant="outlined"
                density="compact"
              />
            </v-col>
            <v-col cols="12" sm="3">
              <v-text-field
                v-model.number="editForm.max_users"
                label="Max Users"
                type="number"
                variant="outlined"
                density="compact"
              />
            </v-col>
            <v-col cols="12" sm="3">
              <v-text-field
                v-model.number="editForm.max_admins"
                label="Max Admins"
                type="number"
                variant="outlined"
                density="compact"
              />
            </v-col>
            <v-col cols="12" sm="6">
              <v-switch
                v-model="editForm.is_active"
                label="Active"
                color="success"
                hide-details
              />
            </v-col>
          </v-row>
        </v-card-text>
        <v-card-actions class="pa-5 pt-0">
          <v-spacer />
          <v-btn variant="text" @click="editDialog = false">Cancel</v-btn>
          <v-btn variant="tonal" color="primary" :loading="saving" @click="saveEdit">Save</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Deactivate Confirm Dialog -->
    <v-dialog v-model="deactivateDialog" max-width="420">
      <v-card rounded="xl">
        <v-card-title class="pa-5 pb-0">
          <v-icon color="error" class="mr-2">mdi-alert-circle</v-icon>Deactivate Tenant
        </v-card-title>
        <v-card-text class="pa-5">
          Are you sure you want to deactivate
          <strong>{{ deactivateTenant?.name }}</strong>? This will prevent all users of this tenant from logging in.
        </v-card-text>
        <v-card-actions class="pa-5 pt-0">
          <v-spacer />
          <v-btn variant="text" @click="deactivateDialog = false">Cancel</v-btn>
          <v-btn variant="elevated" color="error" :loading="saving" @click="doDeactivate">Deactivate</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Snackbar -->
    <v-snackbar v-model="snack.show" :color="snack.color" timeout="3000" location="top right">
      {{ snack.message }}
    </v-snackbar>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { tenantApi } from '@/api/tenant'
import type { Tenant, TenantUpdate } from '@/types'

const router = useRouter()

// ── State ────────────────────────────────────────────────────────────────────
const tenants = ref<Tenant[]>([])
const loading = ref(false)
const saving = ref(false)
const search = ref('')
const filterActive = ref<string | null>(null)

const editDialog = ref(false)
const editTenant = ref<Tenant | null>(null)
const editForm = ref<TenantUpdate>({})

const deactivateDialog = ref(false)
const deactivateTenant = ref<Tenant | null>(null)

const snack = ref({ show: false, message: '', color: 'success' })

// ── Options ──────────────────────────────────────────────────────────────────
const activeOptions = [
  { title: 'Active', value: 'true' },
  { title: 'Inactive', value: 'false' },
]
const planOptions = ['starter', 'growth', 'enterprise']

const headers = [
  { title: 'Name', key: 'name', sortable: true },
  { title: 'Slug', key: 'slug' },
  { title: 'Email', key: 'contact_email' },
  { title: 'Plan', key: 'plan' },
  { title: 'Limits', key: 'limits', sortable: false },
  { title: 'Status', key: 'is_active' },
  { title: 'Created', key: 'created_at', sortable: true },
  { title: 'Actions', key: 'actions', sortable: false, align: 'end' as const },
]

// ── Computed ─────────────────────────────────────────────────────────────────
const filteredTenants = computed(() => {
  let list = tenants.value
  if (filterActive.value !== null && filterActive.value !== undefined) {
    const active = filterActive.value === 'true'
    list = list.filter((t) => t.is_active === active)
  }
  if (search.value) {
    const q = search.value.toLowerCase()
    list = list.filter(
      (t) =>
        t.name.toLowerCase().includes(q) ||
        t.slug.toLowerCase().includes(q) ||
        t.contact_email.toLowerCase().includes(q),
    )
  }
  return list
})

// ── Helpers ──────────────────────────────────────────────────────────────────
function planColor(plan: string) {
  return { starter: 'blue', growth: 'orange', enterprise: 'purple' }[plan] ?? 'grey'
}

function formatDate(dt: string) {
  return new Date(dt).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
}

function showSnack(message: string, color = 'success') {
  snack.value = { show: true, message, color }
}

// ── Data loading ──────────────────────────────────────────────────────────────
async function load() {
  loading.value = true
  try {
    const resp = await tenantApi.list(1, 100)
    tenants.value = resp.items
  } catch {
    showSnack('Failed to load tenants', 'error')
  } finally {
    loading.value = false
  }
}

// ── Edit ─────────────────────────────────────────────────────────────────────
function openEdit(tenant: Tenant) {
  editTenant.value = tenant
  editForm.value = {
    name: tenant.name,
    contact_email: tenant.contact_email,
    contact_person: tenant.contact_person ?? '',
    contact_number: tenant.contact_number ?? '',
    plan: tenant.plan,
    max_users: tenant.max_users,
    max_admins: tenant.max_admins,
    is_active: tenant.is_active,
  }
  editDialog.value = true
}

async function saveEdit() {
  if (!editTenant.value) return
  saving.value = true
  try {
    const updated = await tenantApi.update(editTenant.value.id, editForm.value)
    const idx = tenants.value.findIndex((t) => t.id === updated.id)
    if (idx !== -1) tenants.value[idx] = updated
    editDialog.value = false
    showSnack('Tenant updated successfully')
  } catch (e: any) {
    const detail = e?.response?.data?.detail
    showSnack(typeof detail === 'string' ? detail : 'Failed to update tenant', 'error')
  } finally {
    saving.value = false
  }
}

// ── Deactivate ────────────────────────────────────────────────────────────────
function confirmDeactivate(tenant: Tenant) {
  deactivateTenant.value = tenant
  deactivateDialog.value = true
}

async function doDeactivate() {
  if (!deactivateTenant.value) return
  saving.value = true
  try {
    await tenantApi.deactivate(deactivateTenant.value.id)
    const idx = tenants.value.findIndex((t) => t.id === deactivateTenant.value!.id)
    if (idx !== -1) tenants.value[idx].is_active = false
    deactivateDialog.value = false
    showSnack('Tenant deactivated')
  } catch {
    showSnack('Failed to deactivate tenant', 'error')
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>
