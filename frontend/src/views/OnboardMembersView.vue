<template>
  <div>
    <v-row align="center" class="mb-4">
      <v-col>
        <h1 class="text-h5 font-weight-bold">Onboard Members</h1>
        <p class="text-body-2 text-medium-emphasis mt-1">
          Add individual members or upload a CSV file for bulk onboarding.
        </p>
      </v-col>
    </v-row>

    <v-tabs v-model="tab" color="primary" class="mb-4">
      <v-tab value="single">
        <v-icon start>mdi-account-plus</v-icon>
        Single Member
      </v-tab>
      <v-tab value="bulk">
        <v-icon start>mdi-upload</v-icon>
        Bulk CSV Upload
      </v-tab>
    </v-tabs>

    <v-window v-model="tab">
      <!-- ── Single Member Onboard ───────────────────────────────────────── -->
      <v-window-item value="single">
        <v-card max-width="520" class="pa-6">
          <v-card-title class="px-0 pb-4 text-subtitle-1 font-weight-bold">
            Member Details
          </v-card-title>

          <v-form ref="singleForm" @submit.prevent="submitSingle">
            <v-text-field
              v-model="single.full_name"
              label="Full Name *"
              prepend-inner-icon="mdi-account"
              :rules="[required, minLen2]"
              class="mb-2"
            />
            <v-text-field
              v-model="single.email"
              label="Email Address *"
              prepend-inner-icon="mdi-email"
              type="email"
              :rules="[required, emailRule]"
              class="mb-2"
            />
            <v-text-field
              v-model="single.phone"
              label="Phone (optional)"
              prepend-inner-icon="mdi-phone"
              class="mb-4"
              hint="E.164 format e.g. +919876543210"
              persistent-hint
            />

            <v-alert
              v-if="singleError"
              type="error"
              density="compact"
              class="mb-4"
              closable
              @click:close="singleError = ''"
            >
              {{ singleError }}
            </v-alert>

            <v-btn
              type="submit"
              color="primary"
              :loading="singleLoading"
              block
            >
              Create Member
            </v-btn>
          </v-form>
        </v-card>

        <!-- Success card -->
        <v-dialog v-model="singleSuccessDialog" max-width="460">
          <v-card class="pa-4">
            <v-card-title class="text-h6">
              <v-icon color="success" class="mr-2">mdi-check-circle</v-icon>
              Member Created
            </v-card-title>
            <v-card-text v-if="singleResult">
              <p class="mb-2">
                <strong>{{ singleResult.user.full_name }}</strong> ({{ singleResult.user.email }}) has been onboarded.
              </p>
              <p class="mb-1">An invite email has been sent with the temporary password below:</p>
              <v-alert type="info" density="compact" class="mb-3">
                <div class="d-flex align-center justify-space-between">
                  <span class="font-weight-bold" style="font-family: monospace;">
                    {{ singleResult.temp_password }}
                  </span>
                  <v-btn
                    icon
                    size="small"
                    variant="text"
                    @click="copyPassword(singleResult!.temp_password)"
                  >
                    <v-icon>mdi-content-copy</v-icon>
                  </v-btn>
                </div>
              </v-alert>
              <p class="text-caption text-medium-emphasis">
                This password is shown only once. The member should change it after first login.
              </p>
            </v-card-text>
            <v-card-actions class="justify-end">
              <v-btn variant="tonal" @click="closeSingleDialog">Done</v-btn>
              <v-btn color="primary" @click="onboardAnother">Onboard Another</v-btn>
            </v-card-actions>
          </v-card>
        </v-dialog>
      </v-window-item>

      <!-- ── Bulk CSV Upload ────────────────────────────────────────────── -->
      <v-window-item value="bulk">
        <v-card max-width="720" class="pa-6">
          <v-card-title class="px-0 pb-2 text-subtitle-1 font-weight-bold">
            Upload CSV File
          </v-card-title>
          <p class="text-body-2 text-medium-emphasis mb-4">
            CSV must have a header row with at least <code>full_name</code> and <code>email</code> columns.
            An optional <code>phone</code> column is also supported.
          </p>

          <!-- Template download hint -->
          <v-btn
            variant="text"
            density="compact"
            prepend-icon="mdi-download"
            class="mb-4"
            @click="downloadTemplate"
          >
            Download CSV Template
          </v-btn>

          <!-- File drop zone -->
          <div
            class="drop-zone"
            :class="{ 'drop-zone--active': isDragging }"
            @dragover.prevent="isDragging = true"
            @dragleave.prevent="isDragging = false"
            @drop.prevent="onDrop"
          >
            <v-icon size="48" color="medium-emphasis">mdi-file-upload-outline</v-icon>
            <p class="text-body-2 text-medium-emphasis mt-2">
              Drag &amp; drop a CSV file here, or
            </p>
            <v-btn variant="tonal" density="compact" class="mt-2" @click="triggerFilePicker">
              Browse File
            </v-btn>
            <input
              ref="fileInput"
              type="file"
              accept=".csv,text/csv"
              class="d-none"
              @change="onFileSelected"
            />
            <p v-if="selectedFile" class="text-caption text-success mt-2">
              <v-icon size="14" color="success">mdi-check</v-icon>
              {{ selectedFile.name }}
            </p>
          </div>

          <v-alert
            v-if="bulkError"
            type="error"
            density="compact"
            class="mt-4"
            closable
            @click:close="bulkError = ''"
          >
            {{ bulkError }}
          </v-alert>

          <v-btn
            color="primary"
            :loading="bulkLoading"
            :disabled="!selectedFile"
            class="mt-4"
            block
            @click="submitBulk"
          >
            Upload & Onboard
          </v-btn>
        </v-card>

        <!-- Results table -->
        <v-card v-if="bulkResult" max-width="720" class="mt-6 pa-4">
          <v-card-title class="text-subtitle-1 font-weight-bold px-0 pb-2">
            Upload Results
          </v-card-title>

          <!-- Summary chips -->
          <div class="d-flex ga-2 flex-wrap mb-4">
            <v-chip color="success" variant="tonal" prepend-icon="mdi-check-circle">
              {{ bulkResult.created }} Created
            </v-chip>
            <v-chip color="warning" variant="tonal" prepend-icon="mdi-skip-next">
              {{ bulkResult.skipped }} Skipped
            </v-chip>
            <v-chip color="error" variant="tonal" prepend-icon="mdi-alert-circle">
              {{ bulkResult.errors }} Errors
            </v-chip>
            <v-chip color="default" variant="tonal">
              {{ bulkResult.total }} Total rows
            </v-chip>
          </div>

          <v-data-table
            :items="bulkResult.rows"
            :headers="bulkTableHeaders"
            density="compact"
            items-per-page="25"
          >
            <template #item.status="{ item }">
              <v-chip
                :color="statusColor(item.status)"
                size="x-small"
                variant="tonal"
              >
                {{ item.status }}
              </v-chip>
            </template>
          </v-data-table>
        </v-card>
      </v-window-item>
    </v-window>
  </div>
</template>

<script lang="ts" setup>
import { ref, reactive } from 'vue'
import client from '@/api/client'

// ── Tab state ──────────────────────────────────────────────────────────────────
const tab = ref<'single' | 'bulk'>('single')

// ── Validation rules ────────────────────────────────────────────────────────────
const required = (v: string) => !!v?.trim() || 'Required'
const minLen2 = (v: string) => v?.trim().length >= 2 || 'At least 2 characters'
const emailRule = (v: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v) || 'Invalid email'

// ── Single member ──────────────────────────────────────────────────────────────
interface MemberOnboardResponse {
  user: { id: string; full_name: string; email: string }
  temp_password: string
}

const singleForm = ref()
const singleLoading = ref(false)
const singleError = ref('')
const singleSuccessDialog = ref(false)
const singleResult = ref<MemberOnboardResponse | null>(null)

const single = reactive({ full_name: '', email: '', phone: '' })

async function submitSingle() {
  const { valid } = await singleForm.value.validate()
  if (!valid) return

  singleLoading.value = true
  singleError.value = ''
  try {
    const { data } = await client.post<MemberOnboardResponse>('/users/onboard', {
      full_name: single.full_name.trim(),
      email: single.email.trim().toLowerCase(),
      phone: single.phone.trim() || undefined,
    })
    singleResult.value = data
    singleSuccessDialog.value = true
  } catch (err: any) {
    singleError.value =
      err?.response?.data?.detail ?? 'Failed to create member. Please try again.'
  } finally {
    singleLoading.value = false
  }
}

function copyPassword(pwd: string) {
  navigator.clipboard.writeText(pwd)
}

function closeSingleDialog() {
  singleSuccessDialog.value = false
}

function onboardAnother() {
  singleSuccessDialog.value = false
  single.full_name = ''
  single.email = ''
  single.phone = ''
  singleResult.value = null
  singleForm.value?.reset()
}

// ── Bulk CSV ──────────────────────────────────────────────────────────────────
interface BulkOnboardRow {
  row: number
  email: string
  status: 'created' | 'skipped' | 'error'
  detail?: string
}

interface BulkOnboardResponse {
  total: number
  created: number
  skipped: number
  errors: number
  rows: BulkOnboardRow[]
}

const fileInput = ref<HTMLInputElement>()
const selectedFile = ref<File | null>(null)
const isDragging = ref(false)
const bulkLoading = ref(false)
const bulkError = ref('')
const bulkResult = ref<BulkOnboardResponse | null>(null)

const bulkTableHeaders = [
  { title: 'Row', key: 'row', width: '70' },
  { title: 'Email', key: 'email' },
  { title: 'Status', key: 'status', width: '110' },
  { title: 'Detail', key: 'detail' },
]

function triggerFilePicker() {
  fileInput.value?.click()
}

function onFileSelected(event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files?.[0]) {
    selectedFile.value = input.files[0]
    bulkResult.value = null
    bulkError.value = ''
  }
}

function onDrop(event: DragEvent) {
  isDragging.value = false
  const file = event.dataTransfer?.files?.[0]
  if (file) {
    selectedFile.value = file
    bulkResult.value = null
    bulkError.value = ''
  }
}

async function submitBulk() {
  if (!selectedFile.value) return
  bulkLoading.value = true
  bulkError.value = ''
  try {
    const form = new FormData()
    form.append('file', selectedFile.value)
    const { data } = await client.post<BulkOnboardResponse>('/users/onboard/bulk', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    bulkResult.value = data
  } catch (err: any) {
    bulkError.value =
      err?.response?.data?.detail ?? 'Upload failed. Please check your CSV and try again.'
  } finally {
    bulkLoading.value = false
  }
}

function statusColor(s: string) {
  if (s === 'created') return 'success'
  if (s === 'skipped') return 'warning'
  return 'error'
}

function downloadTemplate() {
  const csv = 'full_name,email,phone\nAnita Kumar,anita@example.com,+919876543210\nRaj Mehta,raj@example.com,\n'
  const blob = new Blob([csv], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'varanbook_members_template.csv'
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<style scoped>
.drop-zone {
  border: 2px dashed rgba(var(--v-theme-on-surface), 0.25);
  border-radius: 12px;
  padding: 36px 24px;
  text-align: center;
  transition: border-color 0.2s, background 0.2s;
  cursor: pointer;
}
.drop-zone--active {
  border-color: rgb(var(--v-theme-primary));
  background: rgba(var(--v-theme-primary), 0.05);
}
</style>
