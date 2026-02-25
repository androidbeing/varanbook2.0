<template>
  <div>
    <div v-if="isPending" class="d-flex justify-center py-12">
      <v-progress-circular indeterminate color="primary" size="48" />
    </div>

    <v-alert v-else-if="isError" type="error" variant="tonal">
      Profile not found or you don't have permission to view it.
    </v-alert>

    <template v-else-if="profile">
      <v-btn prepend-icon="mdi-arrow-left" variant="text" class="mb-4" @click="router.back()">
        Back
      </v-btn>

      <!-- ── Hero card ──────────────────────────────────────────────────── -->
      <v-card rounded="xl" class="mb-5">
        <v-row no-gutters>
          <v-col cols="12" sm="4" md="3">
            <v-img
              :src="profile.photo_visible && (profile as any).profile_photo_url ? (profile as any).profile_photo_url : '/placeholder-avatar.png'"
              height="280"
              cover
              class="rounded-ts-xl rounded-bs-xl"
            />
          </v-col>
          <v-col cols="12" sm="8" md="9" class="d-flex flex-column justify-center pa-6">
            <div class="d-flex align-center ga-2 flex-wrap mb-1">
              <h2 class="text-h5 font-weight-bold">
                {{ profile.full_name || (profile.gender === 'male' ? 'Groom Profile' : 'Bride Profile') }}
              </h2>
              <v-chip :color="profile.status === 'active' ? 'success' : 'warning'" size="small">
                {{ profile.status }}
              </v-chip>
            </div>
            <p class="text-body-1 text-medium-emphasis mb-4">
              {{ ageLabel }}
              <span v-if="profile.profession"> &bull; {{ profile.profession }}</span>
              <span v-if="profile.city"> &bull; {{ profile.city }}<span v-if="profile.state">, {{ profile.state }}</span></span>
            </p>
            <v-row dense>
              <v-col v-for="s in heroStats" :key="s.label" cols="6" sm="3">
                <p class="text-caption text-medium-emphasis mb-0">{{ s.label }}</p>
                <p class="text-body-2 font-weight-medium mb-0">{{ s.value || '—' }}</p>
              </v-col>
            </v-row>
          </v-col>
        </v-row>
      </v-card>

      <!-- ── Sections ───────────────────────────────────────────────────── -->
      <v-expansion-panels multiple variant="accordion" rounded="xl">

        <!-- 1. Personal -->
        <v-expansion-panel>
          <v-expansion-panel-title>
            <v-icon start>mdi-account</v-icon>Personal Details
            <v-chip v-if="!profile.personal_visible" size="x-small" color="warning" class="ml-2">Private</v-chip>
          </v-expansion-panel-title>
          <v-expansion-panel-text>
            <div class="detail-grid">
              <detail-cell v-for="r in personalRows" :key="r.label" :row="r" />
            </div>
          </v-expansion-panel-text>
        </v-expansion-panel>

        <!-- 2. Religious & Cultural -->
        <v-expansion-panel>
          <v-expansion-panel-title>
            <v-icon start>mdi-om</v-icon>Religious &amp; Cultural
          </v-expansion-panel-title>
          <v-expansion-panel-text>
            <div class="detail-grid">
              <detail-cell v-for="r in religiousRows" :key="r.label" :row="r" />
            </div>
          </v-expansion-panel-text>
        </v-expansion-panel>

        <!-- 3. Birth & Horoscope -->
        <v-expansion-panel>
          <v-expansion-panel-title>
            <v-icon start>mdi-star-crescent</v-icon>Birth &amp; Horoscope
            <v-chip v-if="!profile.birth_visible" size="x-small" color="warning" class="ml-2">Private</v-chip>
          </v-expansion-panel-title>
          <v-expansion-panel-text>
            <v-alert v-if="!profile.birth_visible" type="warning" variant="tonal" density="compact" class="mb-4">
              Birth details are kept private by this member.
            </v-alert>
            <div v-else class="detail-grid">
              <detail-cell v-for="r in birthRows" :key="r.label" :row="r" />
            </div>
          </v-expansion-panel-text>
        </v-expansion-panel>

        <!-- 4. Professional -->
        <v-expansion-panel>
          <v-expansion-panel-title>
            <v-icon start>mdi-briefcase</v-icon>Professional Details
            <v-chip v-if="!profile.professional_visible" size="x-small" color="warning" class="ml-2">Private</v-chip>
          </v-expansion-panel-title>
          <v-expansion-panel-text>
            <v-alert v-if="!profile.professional_visible" type="warning" variant="tonal" density="compact" class="mb-4">
              Professional details are kept private by this member.
            </v-alert>
            <div v-else class="detail-grid">
              <detail-cell v-for="r in professionalRows" :key="r.label" :row="r" />
            </div>
          </v-expansion-panel-text>
        </v-expansion-panel>

        <!-- 5. Location -->
        <v-expansion-panel>
          <v-expansion-panel-title>
            <v-icon start>mdi-map-marker</v-icon>Location
          </v-expansion-panel-title>
          <v-expansion-panel-text>
            <div class="detail-grid">
              <detail-cell v-for="r in locationRows" :key="r.label" :row="r" />
            </div>
          </v-expansion-panel-text>
        </v-expansion-panel>

        <!-- 6. Family -->
        <v-expansion-panel>
          <v-expansion-panel-title>
            <v-icon start>mdi-account-group</v-icon>Family Details
            <v-chip v-if="!profile.family_visible" size="x-small" color="warning" class="ml-2">Private</v-chip>
          </v-expansion-panel-title>
          <v-expansion-panel-text>
            <v-alert v-if="!profile.family_visible" type="warning" variant="tonal" density="compact" class="mb-4">
              Family details are kept private by this member.
            </v-alert>
            <div v-else class="detail-grid">
              <detail-cell v-for="r in familyRows" :key="r.label" :row="r" />
            </div>
          </v-expansion-panel-text>
        </v-expansion-panel>

        <!-- 7. Contact -->
        <v-expansion-panel>
          <v-expansion-panel-title>
            <v-icon start>mdi-phone</v-icon>Contact Details
            <v-chip v-if="!profile.contact_visible" size="x-small" color="warning" class="ml-2">Private</v-chip>
          </v-expansion-panel-title>
          <v-expansion-panel-text>
            <v-alert v-if="!profile.contact_visible" type="warning" variant="tonal" density="compact" class="mb-4">
              Contact details are kept private by this member.
            </v-alert>
            <div v-else class="detail-grid">
              <detail-cell v-for="r in contactRows" :key="r.label" :row="r" />
            </div>
          </v-expansion-panel-text>
        </v-expansion-panel>

        <!-- 8. Partner Preferences -->
        <v-expansion-panel>
          <v-expansion-panel-title>
            <v-icon start>mdi-heart-search</v-icon>Partner Preferences
          </v-expansion-panel-title>
          <v-expansion-panel-text>
            <div v-if="prefPending" class="py-4 text-center">
              <v-progress-circular indeterminate size="24" />
            </div>
            <v-alert v-else-if="!pref" type="info" variant="tonal" density="compact">
              No partner preferences set by this member.
            </v-alert>
            <template v-else>
              <!-- Range summary -->
              <v-row dense class="mb-3">
                <v-col cols="12" sm="4">
                  <p class="text-caption text-medium-emphasis mb-0">Age Range</p>
                  <p class="text-body-2 font-weight-medium">
                    {{ pref.age_min ?? '—' }} – {{ pref.age_max ?? '—' }} yrs
                  </p>
                </v-col>
                <v-col cols="12" sm="4">
                  <p class="text-caption text-medium-emphasis mb-0">Height Range</p>
                  <p class="text-body-2 font-weight-medium">
                    {{ pref.height_min_cm ?? '—' }} – {{ pref.height_max_cm ?? '—' }} cm
                  </p>
                </v-col>
                <v-col cols="12" sm="4">
                  <p class="text-caption text-medium-emphasis mb-0">Weight Range</p>
                  <p class="text-body-2 font-weight-medium">
                    {{ pref.weight_min_kg ?? '—' }} – {{ pref.weight_max_kg ?? '—' }} kg
                  </p>
                </v-col>
              </v-row>

              <v-divider class="mb-4" />

              <v-row dense>
                <v-col v-for="pr in prefChipRows" :key="pr.label" cols="12" sm="6" class="mb-3">
                  <p class="text-caption text-medium-emphasis mb-1">{{ pr.label }}</p>
                  <div v-if="pr.chips.length" class="d-flex flex-wrap ga-1">
                    <v-chip v-for="c in pr.chips" :key="c" size="small" variant="tonal" color="primary">
                      {{ c }}
                    </v-chip>
                  </div>
                  <p v-else class="text-body-2 text-medium-emphasis font-italic">Any</p>
                </v-col>
              </v-row>
            </template>
          </v-expansion-panel-text>
        </v-expansion-panel>

      </v-expansion-panels>
    </template>
  </div>
</template>

<script lang="ts" setup>
import { computed, defineComponent, h } from 'vue'
import { useRouter } from 'vue-router'
import { useQuery } from '@tanstack/vue-query'
import { profilesApi, preferencesApi } from '@/api/profiles'

// ── Inline detail-cell component ────────────────────────────────────────────
interface DetailRow { label: string; value: string | null | undefined }

const DetailCell = defineComponent({
  name: 'DetailCell',
  props: { row: { type: Object as () => DetailRow, required: true } },
  setup(props) {
    return () => h('div', { class: 'detail-cell' }, [
      h('p', { class: 'text-caption text-medium-emphasis mb-0' }, props.row.label),
      h('p', { class: 'text-body-2 font-weight-medium mb-0' }, props.row.value || '—'),
    ])
  },
})

// ── Props / router ───────────────────────────────────────────────────────────
const props = defineProps<{ id: string }>()
const router = useRouter()

// ── Queries ──────────────────────────────────────────────────────────────────
const { data: profile, isPending, isError } = useQuery({
  queryKey: computed(() => ['profile', props.id]),
  queryFn: () => profilesApi.get(props.id),
})

const { data: pref, isPending: prefPending } = useQuery({
  queryKey: computed(() => ['pref', props.id]),
  // 404 means no prefs set — treat as null, not an error
  queryFn: () => preferencesApi.get(props.id).catch(() => null),
  enabled: computed(() => !!props.id),
})

// ── Formatters ───────────────────────────────────────────────────────────────
function fmtLabel(v: string | null | undefined): string {
  if (!v) return '—'
  return v.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

function fmtIncome(v: string | null | undefined): string {
  const map: Record<string, string> = {
    below_2l: 'Below ₹2L',
    '2_to_5l': '₹2L – 5L',
    '5_to_10l': '₹5L – 10L',
    '10_to_20l': '₹10L – 20L',
    '20_to_50l': '₹20L – 50L',
    above_50l: 'Above ₹50L',
  }
  return v ? (map[v] ?? fmtLabel(v)) : '—'
}

function fmtHeight(cm: number | null | undefined): string {
  if (!cm) return '—'
  const totalIn = Math.round(cm / 2.54)
  const ft = Math.floor(totalIn / 12)
  const inch = totalIn % 12
  return `${cm} cm (${ft}'${inch}")`
}

// ── Age ──────────────────────────────────────────────────────────────────────
const ageLabel = computed(() => {
  const dob = profile.value?.date_of_birth
  if (!dob) return '—'
  const d = new Date(dob)
  const t = new Date()
  let age = t.getFullYear() - d.getFullYear()
  if (t.getMonth() < d.getMonth() || (t.getMonth() === d.getMonth() && t.getDate() < d.getDate())) age--
  return `${age} yrs`
})

// ── Hero stats (always visible summary) ──────────────────────────────────────
const heroStats = computed(() => {
  const p = profile.value
  if (!p) return []
  return [
    { label: 'Age',           value: ageLabel.value },
    { label: 'Height',        value: fmtHeight(p.height_cm) },
    { label: 'Religion',      value: p.religion },
    { label: 'Caste',         value: p.caste },
    { label: 'Marital',       value: fmtLabel(p.marital_status) },
    { label: 'Mother Tongue', value: p.mother_tongue },
    { label: 'Qualification', value: fmtLabel(p.qualification) },
    { label: 'Income',        value: fmtIncome(p.income_range) },
  ]
})

// ── Section data rows ─────────────────────────────────────────────────────────
const personalRows = computed((): DetailRow[] => {
  const p = profile.value!
  return [
    { label: 'Gender',         value: fmtLabel(p.gender) },
    { label: 'Date of Birth',  value: p.date_of_birth ? new Date(p.date_of_birth).toLocaleDateString('en-IN', { day: '2-digit', month: 'long', year: 'numeric' }) : null },
    { label: 'Age',            value: ageLabel.value },
    { label: 'Height',         value: fmtHeight(p.height_cm) },
    { label: 'Weight',         value: p.weight_kg ? `${p.weight_kg} kg` : null },
    { label: 'Complexion',     value: fmtLabel(p.complexion) },
    { label: 'Blood Group',    value: p.blood_group },
    { label: 'Marital Status', value: fmtLabel(p.marital_status) },
    { label: 'Disabilities',   value: p.disabilities },
  ]
})

const religiousRows = computed((): DetailRow[] => {
  const p = profile.value!
  return [
    { label: 'Religion',      value: p.religion },
    { label: 'Caste',         value: p.caste },
    { label: 'Sub-Caste',     value: p.sub_caste },
    { label: 'Gotra',         value: p.gotra },
    { label: 'Mother Tongue', value: p.mother_tongue },
  ]
})

const birthRows = computed((): DetailRow[] => {
  const p = profile.value!
  return [
    { label: 'Time of Birth',    value: p.time_of_birth },
    { label: 'Birth Place',      value: p.birth_place },
    { label: 'Rashi (Zodiac)',   value: fmtLabel(p.rashi) },
    { label: 'Star (Nakshatra)', value: fmtLabel(p.star) },
    { label: 'Dhosam',           value: fmtLabel(p.dhosam) },
    { label: 'Manglik',          value: p.manglik === null || p.manglik === undefined ? null : p.manglik ? 'Yes' : 'No' },
    { label: 'Horoscope',        value: p.horoscope_key ? 'Available (contact for copy)' : null },
  ]
})

const professionalRows = computed((): DetailRow[] => {
  const p = profile.value!
  return [
    { label: 'Qualification', value: fmtLabel(p.qualification) },
    { label: 'Profession',    value: p.profession },
    { label: 'Working At',    value: p.working_at },
    { label: 'Income Range',  value: fmtIncome(p.income_range) },
  ]
})

const locationRows = computed((): DetailRow[] => {
  const p = profile.value!
  return [
    { label: 'Native Place',     value: p.native_place },
    { label: 'Current Location', value: p.current_location },
    { label: 'City',             value: p.city },
    { label: 'State',            value: p.state },
    { label: 'Country',          value: p.country },
  ]
})

const familyRows = computed((): DetailRow[] => {
  const p = profile.value!
  return [
    { label: "Father's Name",       value: p.father_name },
    { label: "Father's Occupation", value: p.father_occupation },
    { label: "Mother's Name",       value: p.mother_name },
    { label: "Mother's Occupation", value: p.mother_occupation },
    { label: 'Siblings Details',    value: p.siblings_details },
  ]
})

const contactRows = computed((): DetailRow[] => {
  const p = profile.value!
  return [
    { label: 'Mobile',   value: p.mobile },
    { label: 'WhatsApp', value: p.whatsapp },
  ]
})

// ── Partner preference chip rows ──────────────────────────────────────────────
const prefChipRows = computed(() => {
  const pr = pref.value
  if (!pr) return []
  return [
    { label: 'Qualifications',    chips: (pr.qualifications ?? []).map(fmtLabel) },
    { label: 'Income Ranges',     chips: (pr.income_ranges ?? []).map(fmtIncome) },
    { label: 'Marital Statuses',  chips: (pr.marital_statuses ?? []).map(fmtLabel) },
    { label: 'Current Locations', chips: pr.current_locations ?? [] },
    { label: 'Native Locations',  chips: pr.native_locations ?? [] },
    { label: 'Castes',            chips: pr.castes ?? [] },
    { label: 'Religions',         chips: pr.religions ?? [] },
    { label: 'Dhosam',            chips: (pr.dhosam ?? []).map(fmtLabel) },
    { label: 'Rashi',             chips: (pr.rashi ?? []).map(fmtLabel) },
    { label: 'Star',              chips: (pr.star ?? []).map(fmtLabel) },
  ]
})
</script>

<style scoped>
.detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(190px, 1fr));
  gap: 16px 24px;
}
.detail-cell {
  min-width: 0;
}
</style>
