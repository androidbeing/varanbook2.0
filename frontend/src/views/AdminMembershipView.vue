<template>
  <div>
    <!-- ── Header ─────────────────────────────────────────────────────────── -->
    <v-row class="mb-6">
      <v-col>
        <v-card color="primary" rounded="xl" class="pa-6">
          <div class="d-flex align-center justify-space-between flex-wrap ga-4">
            <div class="d-flex align-center ga-4">
              <v-icon size="48" class="opacity-75">mdi-card-account-details-star</v-icon>
              <div>
                <h1 class="text-h5 font-weight-bold">Manage Memberships</h1>
                <p class="text-body-2 opacity-80 mb-0">
                  Assign and manage membership plans for your members.
                </p>
              </div>
            </div>
            <v-btn
              color="white"
              variant="tonal"
              prepend-icon="mdi-plus"
              @click="openAssignDialog"
            >
              Assign Plan
            </v-btn>
          </div>
        </v-card>
      </v-col>
    </v-row>

    <!-- ── Payment Info Preview ─────────────────────────────────────────── -->
    <v-row v-if="paymentInfo && hasPaymentInfo" class="mb-4">
      <v-col cols="12">
        <v-card rounded="xl" variant="outlined">
          <v-card-title class="pa-5 pb-2 text-subtitle-1 font-weight-semibold">
            <v-icon class="mr-2" size="20">mdi-cash-fast</v-icon>Payment Info (visible to members)
          </v-card-title>
          <v-card-text class="pa-5 pt-2">
            <v-row align="center">
              <!-- QR Code -->
              <v-col v-if="qrUrl" cols="12" sm="4" md="3" class="text-center">
                <v-img :src="qrUrl" max-width="180" class="mx-auto rounded-lg" />
                <p class="text-caption text-medium-emphasis mt-2 mb-0">UPI QR Code</p>
              </v-col>

              <!-- UPI Details -->
              <v-col cols="12" :sm="qrUrl ? 8 : 12" :md="qrUrl ? 5 : 8">
                <div class="mb-3" v-if="paymentInfo.upi_name">
                  <div class="text-caption text-medium-emphasis mb-1">UPI Account Name</div>
                  <div class="text-body-1 font-weight-semibold">{{ paymentInfo.upi_name }}</div>
                </div>
                <div class="mb-3" v-if="paymentInfo.upi_id">
                  <div class="text-caption text-medium-emphasis mb-1">UPI ID</div>
                  <v-chip color="primary" variant="tonal" size="default" class="font-weight-medium">
                    {{ paymentInfo.upi_id }}
                  </v-chip>
                </div>
                <div v-if="paymentInfo.tenant_name" class="mb-3">
                  <div class="text-caption text-medium-emphasis mb-1">Pay To</div>
                  <div class="text-body-2">{{ paymentInfo.tenant_name }}</div>
                </div>
              </v-col>

              <!-- WhatsApp -->
              <v-col v-if="paymentInfo.payment_whatsapp" cols="12" :md="qrUrl ? 4 : 4">
                <div class="d-flex align-center ga-2">
                  <v-icon color="green" size="20">mdi-whatsapp</v-icon>
                  <span class="text-body-2">{{ paymentInfo.payment_whatsapp }}</span>
                </div>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- ── Filters ────────────────────────────────────────────────────────── -->
    <v-row class="mb-4" align="center">
      <v-col cols="12" sm="4" md="3">
        <v-select
          v-model="statusFilter"
          :items="statusOptions"
          label="Status"
          variant="outlined"
          density="compact"
          clearable
          hide-details
          @update:model-value="onFilterChange"
        />
      </v-col>
      <v-col cols="12" sm="8" md="5">
        <v-text-field
          v-model="search"
          label="Search member name or email"
          variant="outlined"
          density="compact"
          prepend-inner-icon="mdi-magnify"
          clearable
          hide-details
          @update:model-value="onFilterChange"
        />
      </v-col>
    </v-row>

    <!-- ── Subscriptions Table ────────────────────────────────────────────── -->
    <v-card rounded="xl">
      <v-data-table-server
        v-model:page="page"
        v-model:items-per-page="pageSize"
        :headers="headers"
        :items="rows"
        :items-length="total"
        :loading="loading"
        item-value="id"
        hover
      >
        <!-- Member -->
        <template #item.member="{ item }">
          <div>
            <p class="text-body-2 font-weight-medium mb-0">{{ item.member_name ?? '—' }}</p>
            <p class="text-caption text-medium-emphasis mb-0">{{ item.member_email ?? item.user_id }}</p>
          </div>
        </template>

        <!-- Plan -->
        <template #item.plan_name="{ item }">
          <div>
            <p class="text-body-2 font-weight-medium mb-0">{{ item.plan_name }}</p>
            <p class="text-caption text-medium-emphasis mb-0">{{ item.duration_months }} months</p>
          </div>
        </template>

        <!-- Price -->
        <template #item.price_paid_inr="{ item }">
          ₹{{ Number(item.price_paid_inr).toLocaleString('en-IN') }}
        </template>

        <!-- Status -->
        <template #item.status="{ item }">
          <v-chip
            :color="chipColor(item.status)"
            size="small"
            variant="flat"
          >
            {{ item.status }}
          </v-chip>
        </template>

        <!-- Dates -->
        <template #item.starts_at="{ item }">
          {{ formatDate(item.starts_at) }}
        </template>
        <template #item.expires_at="{ item }">
          {{ formatDate(item.expires_at) }}
        </template>

        <!-- Actions -->
        <template #item.actions="{ item }">
          <v-btn
            v-if="item.status === 'active'"
            size="small"
            variant="tonal"
            color="error"
            :loading="cancellingId === item.id"
            @click="confirmCancel(item)"
          >
            Cancel
          </v-btn>
        </template>

        <!-- Empty state -->
        <template #no-data>
          <div class="text-center pa-6 text-medium-emphasis">
            <v-icon size="48" class="mb-2">mdi-card-off-outline</v-icon>
            <p class="mb-0">No subscriptions found.</p>
          </div>
        </template>
      </v-data-table-server>
    </v-card>

    <!-- ── Assign Plan Dialog ─────────────────────────────────────────────── -->
    <v-dialog v-model="assignDialog" max-width="500" persistent>
      <v-card rounded="xl">
        <v-card-title class="pa-5 pb-2 text-subtitle-1 font-weight-semibold">
          <v-icon class="mr-2" size="20">mdi-plus-circle</v-icon>Assign Membership Plan
        </v-card-title>
        <v-card-text class="pa-5 pt-2">
          <v-form ref="assignForm" v-model="assignValid" @submit.prevent="submitAssign">
            <!-- Member select -->
            <v-autocomplete
              v-model="assignData.user_id"
              :items="members"
              item-title="label"
              item-value="id"
              label="Member"
              variant="outlined"
              density="compact"
              class="mb-3"
              :rules="[required]"
              :loading="loadingMembers"
              no-data-text="No members found"
              clearable
            />

            <!-- Plan select -->
            <v-select
              v-model="assignData.plan_template_id"
              :items="planOptions"
              item-title="label"
              item-value="id"
              label="Plan"
              variant="outlined"
              density="compact"
              class="mb-3"
              :rules="[required]"
            />

            <!-- Start date (optional) -->
            <v-text-field
              v-model="assignData.starts_at"
              label="Start Date (optional, defaults to today)"
              type="date"
              variant="outlined"
              density="compact"
              class="mb-3"
              hint="Leave blank to start immediately"
              persistent-hint
            />

            <!-- Notes -->
            <v-textarea
              v-model="assignData.notes"
              label="Notes (optional)"
              variant="outlined"
              density="compact"
              rows="2"
              class="mb-3"
            />

            <v-alert
              v-if="assignError"
              type="error"
              density="compact"
              class="mb-3"
            >
              {{ assignError }}
            </v-alert>
          </v-form>
        </v-card-text>
        <v-card-actions class="pa-5 pt-0 ga-2">
          <v-spacer />
          <v-btn variant="text" @click="assignDialog = false">Cancel</v-btn>
          <v-btn
            color="primary"
            variant="elevated"
            :loading="assigning"
            :disabled="!assignValid"
            @click="submitAssign"
          >
            Assign
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- ── Cancel Confirm Dialog ──────────────────────────────────────────── -->
    <v-dialog v-model="cancelDialog" max-width="400">
      <v-card rounded="xl">
        <v-card-title class="pa-5 pb-2 text-subtitle-1 font-weight-semibold">
          Cancel Subscription?
        </v-card-title>
        <v-card-text class="pa-5 pt-0 text-body-2 text-medium-emphasis">
          This will immediately cancel the <strong>{{ cancelTarget?.plan_name }}</strong>
          subscription for <strong>{{ cancelTarget?.member_name ?? cancelTarget?.user_id }}</strong>.
          This action cannot be undone.
        </v-card-text>
        <v-card-actions class="pa-5 pt-0 ga-2">
          <v-spacer />
          <v-btn variant="text" @click="cancelDialog = false">Back</v-btn>
          <v-btn
            color="error"
            variant="elevated"
            :loading="!!cancellingId"
            @click="doCancel"
          >
            Cancel Subscription
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, onMounted, watch } from 'vue'
import { membershipApi } from '@/api/membership_plans'
import { useMembershipStore } from '@/stores/membership_plan'
import { filesApi } from '@/api/profiles'
import client from '@/api/client'
import type { Subscription, TenantPaymentInfo } from '@/types'

// ── Types ─────────────────────────────────────────────────────────────────────
interface SubscriptionRow extends Subscription {
  member_name?: string
  member_email?: string
}

// ── Store ─────────────────────────────────────────────────────────────────────
const store = useMembershipStore()

// ── Table state ───────────────────────────────────────────────────────────────
const headers = [
  { title: 'Member', key: 'member', sortable: false },
  { title: 'Plan', key: 'plan_name', sortable: false },
  { title: 'Price Paid', key: 'price_paid_inr', sortable: false },
  { title: 'Status', key: 'status', sortable: false },
  { title: 'Starts', key: 'starts_at', sortable: false },
  { title: 'Expires', key: 'expires_at', sortable: false },
  { title: '', key: 'actions', sortable: false, align: 'end' as const },
]

const rows = ref<SubscriptionRow[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)
const statusFilter = ref<string | null>(null)
const search = ref('')

const statusOptions = ['active', 'expired', 'cancelled']

// ── Members for autocomplete ──────────────────────────────────────────────────
interface MemberOption { id: string; label: string; email: string }
const members = ref<MemberOption[]>([])
const loadingMembers = ref(false)

async function fetchMembers() {
  loadingMembers.value = true
  try {
    // Backend caps page_size at 100; fetch two pages if needed for large tenants
    const res = await client.get('/users/members', { params: { page_size: 100, page: 1 } })
    const data = res.data
    let allItems = data.items ?? []

    // If there are more pages, fetch them sequentially
    const totalPages = Math.ceil((data.total ?? 0) / 100)
    for (let p = 2; p <= totalPages; p++) {
      const more = await client.get('/users/members', { params: { page_size: 100, page: p } })
      allItems = allItems.concat(more.data.items ?? [])
    }

    members.value = allItems.map((u: { id: string; full_name: string; email: string }) => ({
      id: u.id,
      label: `${u.full_name} (${u.email})`,
      email: u.email,
    }))
  } catch (e) {
    console.error('Failed to load members:', e)
  } finally {
    loadingMembers.value = false
  }
}

// ── Plan options ──────────────────────────────────────────────────────────────
const planOptions = computed(() =>
  store.plans.map((p) => ({
    id: p.id,
    label: `${p.name} – ${p.duration_months} months – ₹${Number(p.effective_price_inr).toLocaleString('en-IN')}`,
  })),
)

// ── User id → name/email index built from members list ────────────────────────
const memberIndex = computed<Record<string, MemberOption>>(() =>
  Object.fromEntries(members.value.map((m) => [m.id, m])),
)

// ── Load subscriptions ────────────────────────────────────────────────────────
async function loadSubscriptions() {
  loading.value = true
  try {
    const params: Record<string, unknown> = {
      page: page.value,
      size: pageSize.value,
    }
    if (statusFilter.value) params.status = statusFilter.value
    if (search.value?.trim()) params.search = search.value.trim()

    const res = await membershipApi.listSubscriptions(params)
    rows.value = (res.items ?? []).map((s) => {
      const m = memberIndex.value[s.user_id]
      return {
        ...s,
        member_name: m?.label.split('(')[0].trim() ?? undefined,
        member_email: m?.email ?? undefined,
      }
    })
    total.value = res.total
  } finally {
    loading.value = false
  }
}

watch([page, pageSize], loadSubscriptions)

function onFilterChange() {
  page.value = 1
  loadSubscriptions()
}

// ── Assign dialog ─────────────────────────────────────────────────────────────
const assignDialog = ref(false)
const assignValid = ref(false)
const assigning = ref(false)
const assignError = ref<string | null>(null)
const assignForm = ref()
const assignData = ref({
  user_id: '',
  plan_template_id: '',
  starts_at: '',
  notes: '',
})

function openAssignDialog() {
  assignData.value = { user_id: '', plan_template_id: '', starts_at: '', notes: '' }
  assignError.value = null
  assignDialog.value = true
}

async function submitAssign() {
  if (!assignValid.value) return
  assigning.value = true
  assignError.value = null
  try {
    const payload: { user_id: string; plan_template_id: string; starts_at?: string; notes?: string } = {
      user_id: assignData.value.user_id,
      plan_template_id: assignData.value.plan_template_id,
    }
    if (assignData.value.starts_at) payload.starts_at = assignData.value.starts_at
    if (assignData.value.notes.trim()) payload.notes = assignData.value.notes.trim()
    await membershipApi.createSubscription(payload)
    assignDialog.value = false
    page.value = 1
    await loadSubscriptions()
  } catch (e: unknown) {
    const msg =
      (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
      'Failed to assign plan. Please try again.'
    assignError.value = msg
  } finally {
    assigning.value = false
  }
}

// ── Cancel logic ──────────────────────────────────────────────────────────────
const cancelDialog = ref(false)
const cancelTarget = ref<SubscriptionRow | null>(null)
const cancellingId = ref<string | null>(null)

function confirmCancel(item: SubscriptionRow) {
  cancelTarget.value = item
  cancelDialog.value = true
}

async function doCancel() {
  if (!cancelTarget.value) return
  cancellingId.value = cancelTarget.value.id
  cancelDialog.value = false
  try {
    await membershipApi.cancelSubscription(cancelTarget.value.id)
    await loadSubscriptions()
  } finally {
    cancellingId.value = null
    cancelTarget.value = null
  }
}

// ── Utilities ─────────────────────────────────────────────────────────────────
function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}

function chipColor(status: string): string {
  if (status === 'active') return 'success'
  if (status === 'expired') return 'warning'
  return 'error'
}

const required = (v: string) => !!v || 'Required'

// ── Payment Info Preview ──────────────────────────────────────────────────
const paymentInfo = ref<TenantPaymentInfo | null>(null)
const qrUrl = ref<string | null>(null)

const hasPaymentInfo = computed(() => {
  if (!paymentInfo.value) return false
  return !!(paymentInfo.value.upi_id || paymentInfo.value.upi_name || paymentInfo.value.upi_qr_key || paymentInfo.value.payment_whatsapp)
})

async function loadPaymentInfo() {
  try {
    paymentInfo.value = await membershipApi.getPaymentInfo()
    if (paymentInfo.value?.upi_qr_key) {
      try {
        const { url } = await filesApi.presignGet(paymentInfo.value.upi_qr_key)
        qrUrl.value = url
      } catch { /* QR image may not be accessible */ }
    }
  } catch { /* Payment info may not be configured */ }
}

// ── Init ──────────────────────────────────────────────────────────────────
onMounted(async () => {
  await Promise.all([store.fetchPlans(), fetchMembers(), loadPaymentInfo()])
  await loadSubscriptions()
})
</script>
