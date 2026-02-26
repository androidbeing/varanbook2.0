<template>
  <div>
    <!-- Header -->
    <v-row class="mb-6">
      <v-col>
        <v-card color="primary" rounded="xl" class="pa-6">
          <div class="d-flex align-center flex-wrap gap-4">
            <v-btn
              icon="mdi-arrow-left"
              variant="text"
              color="white"
              @click="router.push('/admin/tenants')"
            />
            <v-icon size="40" class="opacity-75">mdi-office-building-plus</v-icon>
            <div>
              <h1 class="text-h5 font-weight-bold">Create New Tenant</h1>
              <p class="text-body-2 opacity-80 mb-0">Onboard a new matrimonial centre.</p>
            </div>
          </div>
        </v-card>
      </v-col>
    </v-row>

    <v-form ref="formRef" v-model="valid" @submit.prevent="submit">
      <v-row>
        <!-- ── Basic Info ──────────────────────────────────────────────────── -->
        <v-col cols="12">
          <v-card rounded="xl" class="mb-4">
            <v-card-title class="pa-5 pb-2 text-subtitle-1 font-weight-semibold">
              <v-icon class="mr-2" size="20">mdi-information-outline</v-icon>Basic Information
            </v-card-title>
            <v-card-text class="pa-5 pt-2">
              <v-row dense>
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="form.name"
                    label="Centre Name *"
                    variant="outlined"
                    density="compact"
                    :rules="[required, minLen(2)]"
                    placeholder="Sharma Vivah Kendra"
                  />
                </v-col>
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="form.slug"
                    label="Slug (URL identifier) *"
                    variant="outlined"
                    density="compact"
                    :rules="[required, slugRule]"
                    placeholder="sharma-vivah-kendra"
                    hint="Lowercase letters, numbers and hyphens only"
                    persistent-hint
                    @input="form.slug = form.slug.toLowerCase().replace(/[^a-z0-9-]/g, '')"
                  />
                </v-col>
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="form.contact_email"
                    label="Contact Email *"
                    variant="outlined"
                    density="compact"
                    :rules="[required, emailRule]"
                    placeholder="admin@sharmavivah.in"
                    type="email"
                  />
                </v-col>
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="form.domain"
                    label="Domain (optional)"
                    variant="outlined"
                    density="compact"
                    placeholder="sharma.matrimony.in"
                  />
                </v-col>
                <v-col cols="12">
                  <v-text-field
                    v-model="form.address"
                    label="Address (optional)"
                    variant="outlined"
                    density="compact"
                    placeholder="123, Main Street, Chennai"
                  />
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- ── Contact Details ─────────────────────────────────────────────── -->
        <v-col cols="12">
          <v-card rounded="xl" class="mb-4">
            <v-card-title class="pa-5 pb-2 text-subtitle-1 font-weight-semibold">
              <v-icon class="mr-2" size="20">mdi-card-account-phone-outline</v-icon>Contact Details
            </v-card-title>
            <v-card-text class="pa-5 pt-2">
              <v-row dense>
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="form.contact_person"
                    label="Contact Person *"
                    variant="outlined"
                    density="compact"
                    :rules="[required, minLen(2)]"
                    placeholder="Ravi Sharma"
                  />
                </v-col>
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="form.contact_number"
                    label="Contact Number *"
                    variant="outlined"
                    density="compact"
                    :rules="[required, phoneRule]"
                    placeholder="+919876543210"
                  />
                </v-col>
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="form.whatsapp_number"
                    label="WhatsApp Number (optional)"
                    variant="outlined"
                    density="compact"
                    :rules="[optionalPhoneRule]"
                    placeholder="+919876543210"
                  />
                </v-col>
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="form.pin"
                    label="PIN Code *"
                    variant="outlined"
                    density="compact"
                    :rules="[required, pinRule]"
                    placeholder="600001"
                    maxlength="6"
                  />
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- ── Plan & Limits ───────────────────────────────────────────────── -->
        <v-col cols="12">
          <v-card rounded="xl" class="mb-4">
            <v-card-title class="pa-5 pb-2 text-subtitle-1 font-weight-semibold">
              <v-icon class="mr-2" size="20">mdi-ticket-confirmation-outline</v-icon>Plan & Limits
            </v-card-title>
            <v-card-text class="pa-5 pt-2">
              <v-row dense>
                <v-col cols="12" sm="4">
                  <v-select
                    v-model="form.plan"
                    :items="planOptions"
                    label="Plan *"
                    variant="outlined"
                    density="compact"
                    :rules="[required]"
                  />
                </v-col>
                <v-col cols="12" sm="4">
                  <v-text-field
                    v-model.number="form.max_users"
                    label="Max Users *"
                    type="number"
                    variant="outlined"
                    density="compact"
                    :rules="[required, minVal(10)]"
                  />
                </v-col>
                <v-col cols="12" sm="4">
                  <v-text-field
                    v-model.number="form.max_admins"
                    label="Max Admins *"
                    type="number"
                    variant="outlined"
                    density="compact"
                    :rules="[required, minVal(1)]"
                  />
                </v-col>
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="form.upi_id"
                    label="UPI ID (optional)"
                    variant="outlined"
                    density="compact"
                    placeholder="sharma@upi"
                  />
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- ── Initial Admin Account ─────────────────────────────────────── -->
        <v-col cols="12">
          <v-card rounded="xl" class="mb-4" border="primary sm">
            <v-card-title class="pa-5 pb-2 text-subtitle-1 font-weight-semibold text-primary">
              <v-icon class="mr-2" size="20" color="primary">mdi-shield-account</v-icon>Initial Admin Account
            </v-card-title>
            <v-card-subtitle class="px-5 pb-2 text-medium-emphasis">
              This creates the first admin user for the new tenant. Save the password — it won't be shown again.
            </v-card-subtitle>
            <v-card-text class="pa-5 pt-2">
              <v-row dense>
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="admin.full_name"
                    label="Admin Full Name *"
                    variant="outlined"
                    density="compact"
                    :rules="[required, minLen(2)]"
                    placeholder="Ravi Sharma"
                  />
                </v-col>
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="admin.email"
                    label="Admin Email *"
                    variant="outlined"
                    density="compact"
                    :rules="[required, emailRule]"
                    placeholder="admin@sharmavivah.in"
                    type="email"
                  />
                </v-col>
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="admin.password"
                    label="Admin Password *"
                    variant="outlined"
                    density="compact"
                    :rules="[required, passwordRule]"
                    :type="showPwd ? 'text' : 'password'"
                    :append-inner-icon="showPwd ? 'mdi-eye-off' : 'mdi-eye'"
                    @click:append-inner="showPwd = !showPwd"
                    hint="Min 8 chars, uppercase, lowercase, digit, special char"
                    persistent-hint
                  />
                </v-col>
                <v-col cols="12" sm="6" class="d-flex align-center">
                  <v-btn
                    variant="tonal"
                    prepend-icon="mdi-dice-multiple"
                    size="small"
                    @click="generatePassword"
                  >
                    Generate Password
                  </v-btn>
                </v-col>
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="admin.phone"
                    label="Admin Phone (optional)"
                    variant="outlined"
                    density="compact"
                    placeholder="+919876543210"
                  />
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- ── Castes ──────────────────────────────────────────────────────── -->
        <v-col cols="12">
          <v-card rounded="xl" class="mb-6">
            <v-card-title class="pa-5 pb-2 text-subtitle-1 font-weight-semibold">
              <v-icon class="mr-2" size="20">mdi-tag-multiple-outline</v-icon>Caste Categories (optional)
            </v-card-title>
            <v-card-text class="pa-5 pt-2">
              <div class="d-flex flex-wrap gap-2 mb-3">
                <v-chip
                  v-for="(caste, i) in form.castes"
                  :key="i"
                  closable
                  @click:close="form.castes!.splice(i, 1)"
                >
                  {{ caste }}
                </v-chip>
              </div>
              <div class="d-flex gap-2">
                <v-text-field
                  v-model="casteInput"
                  label="Add a caste"
                  variant="outlined"
                  density="compact"
                  hide-details
                  @keydown.enter.prevent="addCaste"
                />
                <v-btn variant="tonal" @click="addCaste">Add</v-btn>
              </div>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- ── Actions ─────────────────────────────────────────────────────── -->
        <v-col cols="12">
          <div class="d-flex justify-end gap-3">
            <v-btn variant="outlined" size="large" @click="router.push('/admin/tenants')">
              Cancel
            </v-btn>
            <v-btn
              type="submit"
              variant="elevated"
              color="primary"
              size="large"
              prepend-icon="mdi-check"
              :loading="saving"
              :disabled="!valid"
            >
              Create Tenant
            </v-btn>
          </div>
        </v-col>
      </v-row>
    </v-form>

    <!-- Snackbar -->
    <v-snackbar v-model="snack.show" :color="snack.color" timeout="4000" location="top right">
      {{ snack.message }}
    </v-snackbar>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { tenantApi } from '@/api/tenant'
import type { TenantCreate } from '@/types'

const router = useRouter()

// ── Form state ────────────────────────────────────────────────────────────────
const formRef = ref()
const valid = ref(false)
const saving = ref(false)
const casteInput = ref('')
const snack = ref({ show: false, message: '', color: 'success' })

const planOptions = [
  { title: 'Starter', value: 'starter' },
  { title: 'Growth', value: 'growth' },
  { title: 'Enterprise', value: 'enterprise' },
]

// ── Admin account ─────────────────────────────────────────────────────────────
const showPwd = ref(false)
const admin = ref({ full_name: '', email: '', password: '', phone: '' })

const form = ref<TenantCreate>({
  name: '',
  slug: '',
  domain: null,
  contact_email: '',
  address: null,
  plan: 'starter',
  max_users: 500,
  max_admins: 5,
  contact_person: '',
  contact_number: '',
  whatsapp_number: null,
  pin: '',
  upi_id: null,
  castes: [],
})

// ── Validation rules ──────────────────────────────────────────────────────────
const required = (v: unknown) => (v !== null && v !== undefined && v !== '') || 'Required'
const minLen = (n: number) => (v: string) => (v && v.length >= n) || `Min ${n} characters`
const minVal = (n: number) => (v: number) => (v >= n) || `Min value is ${n}`
const emailRule = (v: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v) || 'Invalid email'
const slugRule = (v: string) =>
  /^[a-z0-9][a-z0-9-]{1,98}[a-z0-9]$/.test(v) ||
  'Slug must be 3-100 chars, lowercase alphanumeric and hyphens, not starting/ending with hyphen'
const phoneRule = (v: string) =>
  /^\+[1-9]\d{6,14}$/.test(v) || 'Must be E.164 format, e.g. +919876543210'
const optionalPhoneRule = (v: string | null) =>
  !v || /^\+[1-9]\d{6,14}$/.test(v) || 'Must be E.164 format, e.g. +919876543210'
const pinRule = (v: string) => /^\d{6}$/.test(v) || 'Must be a 6-digit PIN'
const passwordRule = (v: string) => {
  if (!v || v.length < 8) return 'Min 8 characters'
  if (!/[A-Z]/.test(v)) return 'Need at least one uppercase letter'
  if (!/[a-z]/.test(v)) return 'Need at least one lowercase letter'
  if (!/[0-9]/.test(v)) return 'Need at least one digit'
  if (!/[!@#$%^&*()\-_=+\[\]{}|;:,.<>?]/.test(v)) return 'Need at least one special character'
  return true
}

function generatePassword() {
  const upper = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
  const lower = 'abcdefghijklmnopqrstuvwxyz'
  const digits = '0123456789'
  const specials = '!@#$%^&*'
  const all = upper + lower + digits + specials
  const rand = (set: string) => set[Math.floor(Math.random() * set.length)]
  const password = [
    rand(upper), rand(lower), rand(digits), rand(specials),
    ...Array.from({ length: 8 }, () => rand(all)),
  ].sort(() => Math.random() - 0.5).join('')
  admin.value.password = password
  showPwd.value = true
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function addCaste() {
  const val = casteInput.value.trim()
  if (val && !form.value.castes?.includes(val)) {
    form.value.castes = [...(form.value.castes ?? []), val]
  }
  casteInput.value = ''
}

function showSnack(message: string, color = 'success') {
  snack.value = { show: true, message, color }
}

// ── Submit ────────────────────────────────────────────────────────────────────
async function submit() {
  const { valid: ok } = await formRef.value.validate()
  if (!ok) return

  saving.value = true
  try {
    // Step 1: create the tenant
    const payload: TenantCreate = {
      ...form.value,
      domain: form.value.domain || null,
      address: form.value.address || null,
      whatsapp_number: form.value.whatsapp_number || null,
      upi_id: form.value.upi_id || null,
      castes: form.value.castes?.length ? form.value.castes : [],
    }
    const tenant = await tenantApi.create(payload)

    // Step 2: create the initial admin user for the tenant
    await tenantApi.createAdmin({
      tenant_id: tenant.id,
      email: admin.value.email,
      password: admin.value.password,
      full_name: admin.value.full_name,
      phone: admin.value.phone || null,
    })

    showSnack('Tenant and admin account created successfully!')
    setTimeout(() => router.push('/admin/tenants'), 1800)
  } catch (e: any) {
    const detail = e?.response?.data?.detail
    showSnack(typeof detail === 'string' ? detail : 'Failed to create tenant', 'error')
  } finally {
    saving.value = false
  }
}
</script>
