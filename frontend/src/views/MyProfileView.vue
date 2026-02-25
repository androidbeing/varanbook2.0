<template>
  <div>
    <h1 class="text-h5 font-weight-bold mb-6">My Profile</h1>

    <div v-if="isPending" class="d-flex justify-center py-12">
      <v-progress-circular indeterminate color="primary" size="48" />
    </div>

    <v-row v-else>
      <!-- ── Sidebar ────────────────────────────────────────────────────── -->
      <v-col cols="12" md="3">
        <v-card rounded="xl" class="text-center pa-4 mb-4" elevation="2">
          <v-avatar size="96" class="mb-3" color="primary">
            <v-icon size="56" color="white">mdi-account</v-icon>
          </v-avatar>
          <p class="text-subtitle-1 font-weight-bold mb-1">{{ fullName || '—' }}</p>
          <v-chip
            :color="profileData?.status === 'active' ? 'success' : 'warning'"
            size="small"
            class="mb-3"
          >
            {{ profileData?.status ?? 'draft' }}
          </v-chip>
          <v-divider class="mb-3" />
          <div class="text-caption text-medium-emphasis text-left">
            <v-icon size="12" color="warning">mdi-lock</v-icon> = visible only to you by default
          </div>
        </v-card>
      </v-col>

      <!-- ── Expansion Panels ──────────────────────────────────────────── -->
      <v-col cols="12" md="9">
        <v-expansion-panels v-model="openPanels" multiple variant="accordion">

          <!-- 1. Personal Details -->
          <v-expansion-panel rounded="xl" class="mb-2">
            <v-expansion-panel-title>
              <v-icon class="mr-2" color="primary">mdi-account-circle</v-icon>
              <span class="font-weight-semibold">Personal Details</span>
            </v-expansion-panel-title>
            <v-expansion-panel-text>
              <v-row class="mt-1">
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="fullName"
                    label="Full Name"
                    variant="outlined"
                    density="comfortable"
                    prepend-inner-icon="mdi-account"
                  />
                </v-col>
                <v-col cols="12" sm="6">
                  <v-select
                    v-model="form.gender"
                    label="Gender"
                    :items="genderOptions"
                    variant="outlined"
                    density="comfortable"
                    prepend-inner-icon="mdi-gender-male-female"
                  />
                </v-col>
                <v-col cols="12" sm="6">
                  <div class="text-caption text-medium-emphasis mb-1">
                    Height: {{ form.height_cm ?? 165 }} cm
                  </div>
                  <v-slider
                    v-model="form.height_cm"
                    :min="60"
                    :max="200"
                    :step="1"
                    color="primary"
                    thumb-label
                    label="Height (cm)"
                  />
                </v-col>
                <v-col cols="12" sm="6">
                  <div class="text-caption text-medium-emphasis mb-1">
                    Weight: {{ form.weight_kg ?? 60 }} kg
                  </div>
                  <v-slider
                    v-model="form.weight_kg"
                    :min="35"
                    :max="120"
                    :step="1"
                    color="primary"
                    thumb-label
                    label="Weight (kg)"
                  />
                </v-col>
                <v-col cols="12" sm="6">
                  <v-select
                    v-model="form.marital_status"
                    label="Marital Status"
                    :items="maritalOptions"
                    variant="outlined"
                    density="comfortable"
                    prepend-inner-icon="mdi-ring"
                  />
                </v-col>
                <v-col cols="12" sm="6">
                  <v-select
                    v-model="form.mother_tongue"
                    label="Mother Tongue"
                    :items="motherTongueOptions"
                    variant="outlined"
                    density="comfortable"
                    prepend-inner-icon="mdi-translate"
                  />
                </v-col>
                <v-col cols="12" sm="6">
                  <v-select
                    v-model="form.religion"
                    label="Religion"
                    :items="religionOptions"
                    variant="outlined"
                    density="comfortable"
                    prepend-inner-icon="mdi-temple-hindu"
                  />
                </v-col>
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="form.caste"
                    label="Caste"
                    variant="outlined"
                    density="comfortable"
                    prepend-inner-icon="mdi-account-group"
                  />
                </v-col>
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="form.sub_caste"
                    label="Sub-Caste"
                    variant="outlined"
                    density="comfortable"
                    prepend-inner-icon="mdi-account-group-outline"
                  />
                </v-col>
              </v-row>
              <v-btn
                color="primary"
                :loading="sec.personal"
                prepend-icon="mdi-content-save"
                class="mt-2"
                @click="savePersonal"
              >
                Save Personal Details
              </v-btn>
            </v-expansion-panel-text>
          </v-expansion-panel>

          <!-- 2. Birth Details -->
          <v-expansion-panel rounded="xl" class="mb-2">
            <v-expansion-panel-title>
              <v-icon class="mr-2" color="indigo">mdi-calendar-star</v-icon>
              <span class="font-weight-semibold">Birth Details</span>
              <v-spacer />
              <v-icon size="16" :color="form.birth_visible ? 'success' : 'warning'" class="mr-2">
                {{ form.birth_visible ? 'mdi-lock-open-variant' : 'mdi-lock' }}
              </v-icon>
            </v-expansion-panel-title>
            <v-expansion-panel-text>
              <v-row class="mt-1">
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="form.date_of_birth"
                    label="Date of Birth"
                    type="date"
                    variant="outlined"
                    density="comfortable"
                    prepend-inner-icon="mdi-calendar"
                  />
                </v-col>
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="form.time_of_birth"
                    label="Time of Birth"
                    type="time"
                    variant="outlined"
                    density="comfortable"
                    prepend-inner-icon="mdi-clock-outline"
                  />
                </v-col>
                <v-col cols="12" sm="6">
                  <v-select
                    v-model="form.rashi"
                    label="Rasi (Zodiac Sign)"
                    :items="rashiOptions"
                    variant="outlined"
                    density="comfortable"
                    prepend-inner-icon="mdi-zodiac-aries"
                    clearable
                  />
                </v-col>
                <v-col cols="12" sm="6">
                  <v-select
                    v-model="form.star"
                    label="Star (Nakshatra)"
                    :items="starOptions"
                    variant="outlined"
                    density="comfortable"
                    prepend-inner-icon="mdi-star-four-points"
                    clearable
                  />
                </v-col>
                <v-col cols="12" sm="6">
                  <v-select
                    v-model="form.dhosam"
                    label="Dhosam"
                    :items="dhosamOptions"
                    variant="outlined"
                    density="comfortable"
                    prepend-inner-icon="mdi-alert-circle-outline"
                    clearable
                  />
                </v-col>
                <v-col cols="12" sm="6">
                  <v-file-input
                    v-model="horoscopeFile"
                    label="Horoscope (PDF or Image)"
                    accept=".pdf,image/*"
                    variant="outlined"
                    density="comfortable"
                    prepend-icon=""
                    prepend-inner-icon="mdi-file-upload-outline"
                    :hint="form.horoscope_key ? 'Horoscope already uploaded' : 'Upload PDF or image'"
                    persistent-hint
                    @update:modelValue="uploadHoroscope"
                  />
                </v-col>
              </v-row>
              <v-btn
                color="indigo"
                :loading="sec.birth"
                prepend-icon="mdi-content-save"
                class="mt-2"
                @click="saveBirth"
              >
                Save Birth Details
              </v-btn>
            </v-expansion-panel-text>
          </v-expansion-panel>

          <!-- 3. Professional Details -->
          <v-expansion-panel rounded="xl" class="mb-2">
            <v-expansion-panel-title>
              <v-icon class="mr-2" color="teal">mdi-briefcase</v-icon>
              <span class="font-weight-semibold">Professional Details</span>
              <v-spacer />
              <v-icon size="16" :color="form.professional_visible ? 'success' : 'warning'" class="mr-2">
                {{ form.professional_visible ? 'mdi-lock-open-variant' : 'mdi-lock' }}
              </v-icon>
            </v-expansion-panel-title>
            <v-expansion-panel-text>
              <v-row class="mt-1">
                <v-col cols="12" sm="6">
                  <v-select
                    v-model="form.qualification"
                    label="Qualification"
                    :items="qualificationOptions"
                    variant="outlined"
                    density="comfortable"
                    prepend-inner-icon="mdi-school"
                    clearable
                  />
                </v-col>
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="form.profession"
                    label="Profession"
                    variant="outlined"
                    density="comfortable"
                    prepend-inner-icon="mdi-account-hard-hat"
                  />
                </v-col>
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="form.working_at"
                    label="Working At (Employer / Organisation)"
                    variant="outlined"
                    density="comfortable"
                    prepend-inner-icon="mdi-office-building"
                  />
                </v-col>
                <v-col cols="12" sm="6">
                  <v-select
                    v-model="form.income_range"
                    label="Income Range"
                    :items="incomeOptions"
                    variant="outlined"
                    density="comfortable"
                    prepend-inner-icon="mdi-currency-inr"
                    clearable
                  />
                </v-col>
              </v-row>
              <v-btn
                color="teal"
                :loading="sec.professional"
                prepend-icon="mdi-content-save"
                class="mt-2"
                @click="saveProfessional"
              >
                Save Professional Details
              </v-btn>
            </v-expansion-panel-text>
          </v-expansion-panel>

          <!-- 4. Family Details -->
          <v-expansion-panel rounded="xl" class="mb-2">
            <v-expansion-panel-title>
              <v-icon class="mr-2" color="orange-darken-2">mdi-home-heart</v-icon>
              <span class="font-weight-semibold">Family Details</span>
              <v-spacer />
              <v-icon size="16" :color="form.family_visible ? 'success' : 'warning'" class="mr-2">
                {{ form.family_visible ? 'mdi-lock-open-variant' : 'mdi-lock' }}
              </v-icon>
            </v-expansion-panel-title>
            <v-expansion-panel-text>
              <v-row class="mt-1">
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="form.father_name"
                    label="Father's Name"
                    variant="outlined"
                    density="comfortable"
                    prepend-inner-icon="mdi-account-tie"
                  />
                </v-col>
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="form.father_occupation"
                    label="Father's Occupation"
                    variant="outlined"
                    density="comfortable"
                    prepend-inner-icon="mdi-briefcase-outline"
                  />
                </v-col>
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="form.mother_name"
                    label="Mother's Name"
                    variant="outlined"
                    density="comfortable"
                    prepend-inner-icon="mdi-account-heart"
                  />
                </v-col>
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="form.mother_occupation"
                    label="Mother's Occupation"
                    variant="outlined"
                    density="comfortable"
                    prepend-inner-icon="mdi-briefcase-outline"
                  />
                </v-col>
                <v-col cols="12">
                  <v-textarea
                    v-model="form.siblings_details"
                    label="Siblings Details (e.g. 2 brothers, 1 sister married)"
                    rows="2"
                    variant="outlined"
                    density="comfortable"
                    prepend-inner-icon="mdi-account-multiple"
                  />
                </v-col>
              </v-row>
              <v-btn
                color="orange-darken-2"
                :loading="sec.family"
                prepend-icon="mdi-content-save"
                class="mt-2"
                @click="saveFamily"
              >
                Save Family Details
              </v-btn>
            </v-expansion-panel-text>
          </v-expansion-panel>

          <!-- 5. Contact Details -->
          <v-expansion-panel rounded="xl" class="mb-2">
            <v-expansion-panel-title>
              <v-icon class="mr-2" color="blue-darken-2">mdi-phone</v-icon>
              <span class="font-weight-semibold">Contact Details</span>
              <v-spacer />
              <v-icon size="16" :color="form.contact_visible ? 'success' : 'warning'" class="mr-2">
                {{ form.contact_visible ? 'mdi-lock-open-variant' : 'mdi-lock' }}
              </v-icon>
            </v-expansion-panel-title>
            <v-expansion-panel-text>
              <v-row class="mt-1">
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="form.mobile"
                    label="Mobile Number"
                    variant="outlined"
                    density="comfortable"
                    prepend-inner-icon="mdi-cellphone"
                    hint="10-digit (7558112327) or with code (+917558112327)"
                    persistent-hint
                  />
                </v-col>
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="form.whatsapp"
                    label="WhatsApp Number"
                    variant="outlined"
                    density="comfortable"
                    prepend-inner-icon="mdi-whatsapp"
                    hint="10-digit (7558112327) or with code (+917558112327)"
                    persistent-hint
                  />
                </v-col>
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="form.native_place"
                    label="Native Place"
                    variant="outlined"
                    density="comfortable"
                    prepend-inner-icon="mdi-map-marker-outline"
                  />
                </v-col>
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="form.current_location"
                    label="Current Location"
                    variant="outlined"
                    density="comfortable"
                    prepend-inner-icon="mdi-map-marker"
                  />
                </v-col>
              </v-row>
              <v-btn
                color="blue-darken-2"
                :loading="sec.contact"
                prepend-icon="mdi-content-save"
                class="mt-2"
                @click="saveContact"
              >
                Save Contact Details
              </v-btn>
            </v-expansion-panel-text>
          </v-expansion-panel>

          <!-- 6. Photos -->
          <v-expansion-panel rounded="xl" class="mb-2">
            <v-expansion-panel-title>
              <v-icon class="mr-2" color="pink-darken-2">mdi-image-multiple</v-icon>
              <span class="font-weight-semibold">Photos</span>
              <v-chip size="x-small" class="ml-2" color="grey">
                {{ (form.photo_keys || []).length }} / 10
              </v-chip>
              <v-spacer />
              <v-icon size="16" :color="form.photo_visible ? 'success' : 'warning'" class="mr-2">
                {{ form.photo_visible ? 'mdi-lock-open-variant' : 'mdi-lock' }}
              </v-icon>
            </v-expansion-panel-title>
            <v-expansion-panel-text>
              <div class="d-flex flex-wrap ga-3 mb-4">
                <v-card
                  v-for="(key, i) in (form.photo_keys || [])"
                  :key="key"
                  width="90"
                  height="90"
                  rounded="lg"
                  class="d-flex flex-column align-center justify-center"
                  color="grey-lighten-3"
                  elevation="0"
                >
                  <v-icon color="grey-darken-1" size="28">mdi-image</v-icon>
                  <span class="text-caption text-medium-emphasis mt-1">Photo {{ i + 1 }}</span>
                </v-card>
                <v-card
                  v-if="(form.photo_keys || []).length < 10"
                  width="90"
                  height="90"
                  rounded="lg"
                  class="d-flex align-center justify-center cursor-pointer hover-border"
                  color="grey-lighten-5"
                  border
                  elevation="0"
                  @click="photoInput?.click()"
                >
                  <v-icon color="primary" size="32">mdi-plus-circle-outline</v-icon>
                </v-card>
              </div>
              <input ref="photoInput" type="file" accept="image/*" multiple style="display:none" @change="uploadPhotos" />
              <p class="text-caption text-medium-emphasis">
                Upload up to 10 photos. Supported formats: JPG, PNG, WebP.
                Requires cloud storage (S3) to be configured.
              </p>
            </v-expansion-panel-text>
          </v-expansion-panel>

          <!-- 7. Privacy Controls -->
          <v-expansion-panel rounded="xl" class="mb-2">
            <v-expansion-panel-title>
              <v-icon class="mr-2" color="deep-purple">mdi-shield-lock</v-icon>
              <span class="font-weight-semibold">Privacy Controls</span>
            </v-expansion-panel-title>
            <v-expansion-panel-text>
              <v-alert type="info" variant="tonal" density="compact" class="mb-4">
                Personal details are always visible. Toggle sections below to control what others can see.
              </v-alert>
              <v-list lines="two" class="pa-0">
                <v-list-item
                  title="Photos"
                  subtitle="Allow other members to see your photos"
                  rounded="lg"
                  class="mb-1"
                >
                  <template #append>
                    <v-switch v-model="form.photo_visible" color="primary" hide-details inset />
                  </template>
                </v-list-item>
                <v-divider />
                <v-list-item
                  title="Birth Details"
                  subtitle="Rasi, Star, Dhosam and horoscope document"
                  rounded="lg"
                  class="mb-1"
                >
                  <template #append>
                    <v-switch v-model="form.birth_visible" color="primary" hide-details inset />
                  </template>
                </v-list-item>
                <v-divider />
                <v-list-item
                  title="Professional Details"
                  subtitle="Qualification, employer and income range"
                  rounded="lg"
                  class="mb-1"
                >
                  <template #append>
                    <v-switch v-model="form.professional_visible" color="primary" hide-details inset />
                  </template>
                </v-list-item>
                <v-divider />
                <v-list-item
                  title="Family Details"
                  subtitle="Parents names, occupations, siblings"
                  rounded="lg"
                  class="mb-1"
                >
                  <template #append>
                    <v-switch v-model="form.family_visible" color="primary" hide-details inset />
                  </template>
                </v-list-item>
                <v-divider />
                <v-list-item
                  title="Contact Details"
                  subtitle="Mobile, WhatsApp and location"
                  rounded="lg"
                  class="mb-1"
                >
                  <template #append>
                    <v-switch v-model="form.contact_visible" color="primary" hide-details inset />
                  </template>
                </v-list-item>
                <v-divider />
                <v-list-item
                  title="Horoscope Document"
                  subtitle="PDF or image of your horoscope chart"
                  rounded="lg"
                >
                  <template #append>
                    <v-switch v-model="form.horoscope_visible" color="primary" hide-details inset />
                  </template>
                </v-list-item>
              </v-list>
              <v-btn
                color="deep-purple"
                :loading="sec.privacy"
                prepend-icon="mdi-content-save"
                class="mt-4"
                @click="savePrivacy"
              >
                Save Privacy Settings
              </v-btn>
            </v-expansion-panel-text>
          </v-expansion-panel>

          <!-- 8. Partner Preferences -->
          <v-expansion-panel rounded="xl" class="mb-2">
            <v-expansion-panel-title>
              <v-icon class="mr-2" color="red-darken-2">mdi-heart-search</v-icon>
              <span class="font-weight-semibold">Partner Preferences</span>
            </v-expansion-panel-title>
            <v-expansion-panel-text>
              <v-row class="mt-1">
                <!-- Age Range -->
                <v-col cols="12" sm="6">
                  <div class="text-caption text-medium-emphasis mb-1">
                    Age Range: {{ ageRange[0] }} – {{ ageRange[1] }} years
                  </div>
                  <v-range-slider
                    v-model="ageRange"
                    :min="18"
                    :max="80"
                    :step="1"
                    color="primary"
                    strict
                    hide-details
                  />
                </v-col>
                <!-- Height Range -->
                <v-col cols="12" sm="6">
                  <div class="text-caption text-medium-emphasis mb-1">
                    Height Range: {{ heightRange[0] }} – {{ heightRange[1] }} cm
                  </div>
                  <v-range-slider
                    v-model="heightRange"
                    :min="60"
                    :max="200"
                    :step="1"
                    color="primary"
                    strict
                    hide-details
                  />
                </v-col>
                <!-- Weight Range -->
                <v-col cols="12" sm="6">
                  <div class="text-caption text-medium-emphasis mb-1">
                    Weight Range: {{ weightRange[0] }} – {{ weightRange[1] }} kg
                  </div>
                  <v-range-slider
                    v-model="weightRange"
                    :min="35"
                    :max="120"
                    :step="1"
                    color="primary"
                    strict
                    hide-details
                  />
                </v-col>
                <!-- Qualification -->
                <v-col cols="12" sm="6">
                  <v-select
                    v-model="prefForm.qualifications"
                    label="Qualification"
                    :items="qualificationOptions"
                    multiple
                    chips
                    closable-chips
                    variant="outlined"
                    density="comfortable"
                    prepend-inner-icon="mdi-school"
                  />
                </v-col>
                <!-- Income Range -->
                <v-col cols="12" sm="6">
                  <v-select
                    v-model="prefForm.income_ranges"
                    label="Income Range"
                    :items="incomeOptions"
                    multiple
                    chips
                    closable-chips
                    variant="outlined"
                    density="comfortable"
                    prepend-inner-icon="mdi-currency-inr"
                  />
                </v-col>
                <!-- Current Locations -->
                <v-col cols="12" sm="6">
                  <v-combobox
                    v-model="prefForm.current_locations"
                    label="Current Location(s)"
                    multiple
                    chips
                    closable-chips
                    variant="outlined"
                    density="comfortable"
                    prepend-inner-icon="mdi-map-marker"
                    hint="Type a city/district and press Enter"
                    persistent-hint
                  />
                </v-col>
                <!-- Native Locations -->
                <v-col cols="12" sm="6">
                  <v-combobox
                    v-model="prefForm.native_locations"
                    label="Native Location(s)"
                    multiple
                    chips
                    closable-chips
                    variant="outlined"
                    density="comfortable"
                    prepend-inner-icon="mdi-map-marker-outline"
                    hint="Type a place and press Enter"
                    persistent-hint
                  />
                </v-col>
                <!-- Dhosam -->
                <v-col cols="12" sm="6">
                  <v-select
                    v-model="prefForm.dhosam"
                    label="Dhosam (acceptable)"
                    :items="dhosamOptions"
                    multiple
                    chips
                    closable-chips
                    variant="outlined"
                    density="comfortable"
                    prepend-inner-icon="mdi-alert-circle-outline"
                  />
                </v-col>
                <!-- Rasi -->
                <v-col cols="12" sm="6">
                  <v-select
                    v-model="prefForm.rashi"
                    label="Rasi (preferred)"
                    :items="rashiOptions"
                    multiple
                    chips
                    closable-chips
                    variant="outlined"
                    density="comfortable"
                    prepend-inner-icon="mdi-zodiac-aries"
                  />
                </v-col>
                <!-- Star -->
                <v-col cols="12">
                  <v-select
                    v-model="prefForm.star"
                    label="Star / Nakshatra (preferred)"
                    :items="starOptions"
                    multiple
                    chips
                    closable-chips
                    variant="outlined"
                    density="comfortable"
                    prepend-inner-icon="mdi-star-four-points"
                  />
                </v-col>
              </v-row>
              <v-btn
                color="red-darken-2"
                :loading="sec.prefs"
                prepend-icon="mdi-content-save"
                class="mt-2"
                @click="savePreferences"
              >
                Save Partner Preferences
              </v-btn>
            </v-expansion-panel-text>
          </v-expansion-panel>

        </v-expansion-panels>
      </v-col>
    </v-row>

    <!-- Success / Error Snackbar -->
    <v-snackbar v-model="snack.show" :color="snack.color" timeout="3000" location="bottom right">
      {{ snack.message }}
    </v-snackbar>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useQuery, useQueryClient } from '@tanstack/vue-query'
import { profilesApi, preferencesApi, usersApi } from '@/api/profiles'
import { useAuthStore } from '@/stores/auth'
import type { Profile, PartnerPreference } from '@/types'

const authStore = useAuthStore()
const authUser = computed(() => authStore.user)
const qc = useQueryClient()

// ── Profile query ────────────────────────────────────────────────────────────
const { data: profileData, isPending } = useQuery({
  queryKey: ['my-profile'],
  queryFn: () => profilesApi.mine(),
  retry: false,
  staleTime: 60_000,   // keep cache fresh for 60 s to survive navigation
})

// ── State ────────────────────────────────────────────────────────────────────
const fullName = ref('')
const openPanels = ref([0])
const photoInput = ref<HTMLInputElement | null>(null)
const horoscopeFile = ref<File[]>([])
const sec = ref({ personal: false, birth: false, professional: false, family: false, contact: false, privacy: false, prefs: false })
const snack = ref({ show: false, color: 'success', message: '' })

// ── Profile form ─────────────────────────────────────────────────────────────
const form = ref<Partial<Profile>>({
  gender: null,
  height_cm: 165,
  weight_kg: 60,
  marital_status: 'never_married',
  mother_tongue: null,
  religion: null,
  caste: '',
  sub_caste: '',
  date_of_birth: null,
  time_of_birth: null,
  rashi: null,
  star: null,
  dhosam: null,
  horoscope_key: null,
  qualification: null,
  profession: '',
  working_at: '',
  income_range: null,
  father_name: '',
  father_occupation: '',
  mother_name: '',
  mother_occupation: '',
  siblings_details: '',
  mobile: '',
  whatsapp: '',
  native_place: '',
  current_location: '',
  photo_keys: [],
  personal_visible: true,
  photo_visible: false,
  birth_visible: false,
  professional_visible: false,
  family_visible: false,
  contact_visible: false,
  horoscope_visible: false,
})

// ── Partner preferences form ──────────────────────────────────────────────────
const prefForm = ref<Partial<PartnerPreference>>({
  age_min: 22,
  age_max: 35,
  height_min_cm: 150,
  height_max_cm: 185,
  weight_min_kg: 45,
  weight_max_kg: 90,
  qualifications: [],
  income_ranges: [],
  marital_statuses: [],
  current_locations: [],
  native_locations: [],
  dhosam: [],
  rashi: [],
  star: [],
})

// ── Range slider computed helpers ─────────────────────────────────────────────
const ageRange = computed({
  get: (): [number, number] => [prefForm.value.age_min ?? 22, prefForm.value.age_max ?? 35],
  set: (v: [number, number]) => { prefForm.value.age_min = v[0]; prefForm.value.age_max = v[1] },
})
const heightRange = computed({
  get: (): [number, number] => [prefForm.value.height_min_cm ?? 150, prefForm.value.height_max_cm ?? 185],
  set: (v: [number, number]) => { prefForm.value.height_min_cm = v[0]; prefForm.value.height_max_cm = v[1] },
})
const weightRange = computed({
  get: (): [number, number] => [prefForm.value.weight_min_kg ?? 45, prefForm.value.weight_max_kg ?? 90],
  set: (v: [number, number]) => { prefForm.value.weight_min_kg = v[0]; prefForm.value.weight_max_kg = v[1] },
})

// ── Helpers ───────────────────────────────────────────────────────────────────
function populateFormFromProfile(p: Profile | null | undefined) {
  if (!p) return
  const keys = Object.keys(form.value) as (keyof Profile)[]
  keys.forEach((k) => { if (k in p) (form.value as any)[k] = (p as any)[k] })
  // Also restore the display name from the profile response (belt-and-suspenders
  // fallback in case authStore.user hasn't resolved yet on remount)
  if (p.full_name) fullName.value = p.full_name
}

async function populatePrefForm(p: Profile | null | undefined) {
  if (!p) return
  try {
    const pref = await preferencesApi.get(p.id)
    Object.assign(prefForm.value, pref)
  } catch {
    // 404 = no preferences set yet – ignore
  }
}

// ── Watchers ─────────────────────────────────────────────────────────────────
watch(profileData, populateFormFromProfile, { immediate: true })

watch(authUser, (u) => { if (u?.full_name) fullName.value = u.full_name }, { immediate: true })

watch(profileData, populatePrefForm, { immediate: true })

// Backup: populate from cache on mount in case the immediate watcher
// fired before TanStack Query had resolved the cached value into the ref.
onMounted(() => {
  populateFormFromProfile(profileData.value)
  if (authStore.user?.full_name) fullName.value = authStore.user.full_name
  populatePrefForm(profileData.value)
})

// ── Utilities ─────────────────────────────────────────────────────────────────
function notify(message: string, color = 'success') {
  snack.value = { show: true, color, message }
}

// ── Save handlers ─────────────────────────────────────────────────────────────
async function savePersonal() {
  sec.value.personal = true
  try {
    await usersApi.updateMe({ full_name: fullName.value })
    const exists = !!profileData.value
    const payload = {
      gender: form.value.gender,
      height_cm: form.value.height_cm,
      weight_kg: form.value.weight_kg,
      marital_status: form.value.marital_status,
      mother_tongue: form.value.mother_tongue,
      religion: form.value.religion,
      caste: form.value.caste,
      sub_caste: form.value.sub_caste,
    }
    if (exists) {
      await profilesApi.updateMe(payload)
    } else {
      await profilesApi.create({ ...payload, date_of_birth: form.value.date_of_birth ?? undefined })
    }
    await qc.invalidateQueries({ queryKey: ['my-profile'] })
    notify('Personal details saved!')
  } catch {
    notify('Failed to save personal details.', 'error')
  } finally {
    sec.value.personal = false
  }
}

async function saveBirth() {
  sec.value.birth = true
  try {
    await profilesApi.updateMe({
      date_of_birth: form.value.date_of_birth,
      time_of_birth: form.value.time_of_birth,
      rashi: form.value.rashi,
      star: form.value.star,
      dhosam: form.value.dhosam,
    })
    await qc.invalidateQueries({ queryKey: ['my-profile'] })
    notify('Birth details saved!')
  } catch {
    notify('Failed to save birth details.', 'error')
  } finally {
    sec.value.birth = false
  }
}

async function saveProfessional() {
  sec.value.professional = true
  try {
    await profilesApi.updateMe({
      qualification: form.value.qualification,
      profession: form.value.profession,
      working_at: form.value.working_at,
      income_range: form.value.income_range,
    })
    await qc.invalidateQueries({ queryKey: ['my-profile'] })
    notify('Professional details saved!')
  } catch {
    notify('Failed to save professional details.', 'error')
  } finally {
    sec.value.professional = false
  }
}

async function saveFamily() {
  sec.value.family = true
  try {
    await profilesApi.updateMe({
      father_name: form.value.father_name,
      father_occupation: form.value.father_occupation,
      mother_name: form.value.mother_name,
      mother_occupation: form.value.mother_occupation,
      siblings_details: form.value.siblings_details,
    })
    await qc.invalidateQueries({ queryKey: ['my-profile'] })
    notify('Family details saved!')
  } catch {
    notify('Failed to save family details.', 'error')
  } finally {
    sec.value.family = false
  }
}

/** Normalise a phone number to E.164. Bare 10-digit Indian numbers get +91. */
function toE164(num: string | null | undefined): string | null {
  if (!num) return null
  const clean = num.replace(/[\s\-\(\)]/g, '')
  if (/^[6-9]\d{9}$/.test(clean)) return '+91' + clean
  return clean
}

async function saveContact() {
  sec.value.contact = true
  try {
    await profilesApi.updateMe({
      mobile: toE164(form.value.mobile),
      whatsapp: toE164(form.value.whatsapp),
      native_place: form.value.native_place,
      current_location: form.value.current_location,
    })
    await qc.invalidateQueries({ queryKey: ['my-profile'] })
    notify('Contact details saved!')
  } catch {
    notify('Failed to save contact details.', 'error')
  } finally {
    sec.value.contact = false
  }
}

async function savePrivacy() {
  sec.value.privacy = true
  try {
    await profilesApi.updateMe({
      photo_visible: form.value.photo_visible,
      birth_visible: form.value.birth_visible,
      professional_visible: form.value.professional_visible,
      family_visible: form.value.family_visible,
      contact_visible: form.value.contact_visible,
      horoscope_visible: form.value.horoscope_visible,
    })
    await qc.invalidateQueries({ queryKey: ['my-profile'] })
    notify('Privacy settings saved!')
  } catch {
    notify('Failed to save privacy settings.', 'error')
  } finally {
    sec.value.privacy = false
  }
}

async function savePreferences() {
  if (!profileData.value) return
  sec.value.prefs = true
  try {
    await preferencesApi.upsert(profileData.value.id, prefForm.value)
    notify('Partner preferences saved!')
  } catch {
    notify('Failed to save partner preferences.', 'error')
  } finally {
    sec.value.prefs = false
  }
}

async function uploadHoroscope() {
  if (!horoscopeFile.value?.[0] || !profileData.value) return
  const file = horoscopeFile.value[0]
  try {
    const { upload_url, object_key } = await profilesApi.presign({
      file_name: file.name,
      content_type: file.type || 'application/pdf',
      upload_purpose: 'horoscope',
    })
    await fetch(upload_url, { method: 'PUT', body: file, headers: { 'Content-Type': file.type } })
    await profilesApi.registerMedia(profileData.value.id, object_key, 'horoscope')
    form.value.horoscope_key = object_key
    notify('Horoscope uploaded successfully!')
  } catch {
    notify('Horoscope upload failed. Cloud storage may not be configured.', 'warning')
  }
}

async function uploadPhotos(e: Event) {
  if (!profileData.value) return
  const files = Array.from((e.target as HTMLInputElement).files ?? [])
  if (!files.length) return
  const existing = form.value.photo_keys?.length ?? 0
  const allowed = Math.min(files.length, 10 - existing)
  let uploaded = 0
  for (const file of files.slice(0, allowed)) {
    try {
      const { upload_url, object_key } = await profilesApi.presign({
        file_name: file.name,
        content_type: file.type,
        upload_purpose: 'profile_photo',
      })
      await fetch(upload_url, { method: 'PUT', body: file, headers: { 'Content-Type': file.type } })
      await profilesApi.registerMedia(profileData.value.id, object_key, 'profile_photo')
      form.value.photo_keys = [...(form.value.photo_keys ?? []), object_key]
      uploaded++
    } catch {
      notify('Photo upload failed. Cloud storage may not be configured.', 'warning')
      break
    }
  }
  if (uploaded > 0) {
    await qc.invalidateQueries({ queryKey: ['my-profile'] })
    notify(`${uploaded} photo(s) uploaded!`)
  }
}

// ── Dropdown options ──────────────────────────────────────────────────────────
const genderOptions = [
  { title: 'Male', value: 'male' },
  { title: 'Female', value: 'female' },
  { title: 'Other', value: 'other' },
]

const maritalOptions = [
  { title: 'Never Married', value: 'never_married' },
  { title: 'Divorced', value: 'divorced' },
  { title: 'Widowed', value: 'widowed' },
  { title: 'Awaiting Divorce', value: 'awaiting_divorce' },
]

const motherTongueOptions = [
  'Tamil', 'Telugu', 'Kannada', 'Malayalam', 'Hindi',
  'English', 'Marathi', 'Bengali', 'Gujarati', 'Punjabi', 'Others',
]

const religionOptions = [
  'Hindu', 'Muslim', 'Christian', 'Jain', 'Buddhist', 'Sikh', 'Others',
]

const rashiOptions = [
  { title: 'Mesha (Aries)', value: 'mesha' },
  { title: 'Vrishabha (Taurus)', value: 'vrishabha' },
  { title: 'Mithuna (Gemini)', value: 'mithuna' },
  { title: 'Karka (Cancer)', value: 'karka' },
  { title: 'Simha (Leo)', value: 'simha' },
  { title: 'Kanya (Virgo)', value: 'kanya' },
  { title: 'Tula (Libra)', value: 'tula' },
  { title: 'Vrishchika (Scorpio)', value: 'vrishchika' },
  { title: 'Dhanu (Sagittarius)', value: 'dhanu' },
  { title: 'Makara (Capricorn)', value: 'makara' },
  { title: 'Kumbha (Aquarius)', value: 'kumbha' },
  { title: 'Meena (Pisces)', value: 'meena' },
]

const starOptions = [
  { title: 'Ashwini', value: 'ashwini' },
  { title: 'Bharani', value: 'bharani' },
  { title: 'Krittika', value: 'krittika' },
  { title: 'Rohini', value: 'rohini' },
  { title: 'Mrigashira', value: 'mrigashira' },
  { title: 'Ardra', value: 'ardra' },
  { title: 'Punarvasu', value: 'punarvasu' },
  { title: 'Pushya', value: 'pushya' },
  { title: 'Ashlesha', value: 'ashlesha' },
  { title: 'Magha', value: 'magha' },
  { title: 'Purva Phalguni', value: 'purva_phalguni' },
  { title: 'Uttara Phalguni', value: 'uttara_phalguni' },
  { title: 'Hasta', value: 'hasta' },
  { title: 'Chitra', value: 'chitra' },
  { title: 'Swati', value: 'swati' },
  { title: 'Vishakha', value: 'vishakha' },
  { title: 'Anuradha', value: 'anuradha' },
  { title: 'Jyeshtha', value: 'jyeshtha' },
  { title: 'Moola', value: 'moola' },
  { title: 'Purva Ashadha', value: 'purva_ashadha' },
  { title: 'Uttara Ashadha', value: 'uttara_ashadha' },
  { title: 'Shravana', value: 'shravana' },
  { title: 'Dhanishtha', value: 'dhanishtha' },
  { title: 'Shatabhisha', value: 'shatabhisha' },
  { title: 'Purva Bhadrapada', value: 'purva_bhadrapada' },
  { title: 'Uttara Bhadrapada', value: 'uttara_bhadrapada' },
  { title: 'Revati', value: 'revati' },
]

const dhosamOptions = [
  { title: 'None', value: 'none' },
  { title: 'Chevvai Dhosam', value: 'chevvai' },
  { title: 'Rahu Dhosam', value: 'rahu' },
  { title: 'Kethu Dhosam', value: 'kethu' },
  { title: 'Shani Dhosam', value: 'shani' },
  { title: 'Multiple', value: 'multiple' },
]

const qualificationOptions = [
  { title: 'Below 10th', value: 'below_10th' },
  { title: 'SSLC (10th)', value: 'sslc' },
  { title: 'HSC (12th)', value: 'hsc' },
  { title: 'Diploma', value: 'diploma' },
  { title: "Bachelor's Degree", value: 'bachelor' },
  { title: "Master's Degree", value: 'master' },
  { title: 'Doctorate (PhD)', value: 'doctorate' },
  { title: 'Professional (CA / CS / ICWA)', value: 'professional' },
  { title: 'Other', value: 'other' },
]

const incomeOptions = [
  { title: 'Below 2 Lakh / year', value: 'below_2l' },
  { title: '2 – 5 Lakh / year', value: '2_to_5l' },
  { title: '5 – 10 Lakh / year', value: '5_to_10l' },
  { title: '10 – 20 Lakh / year', value: '10_to_20l' },
  { title: '20 – 50 Lakh / year', value: '20_to_50l' },
  { title: 'Above 50 Lakh / year', value: 'above_50l' },
]
</script>
