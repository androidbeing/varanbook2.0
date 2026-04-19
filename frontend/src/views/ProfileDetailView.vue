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
      <v-card rounded="xl" class="mb-5 hero-card" elevation="2">
        <!-- Gender accent bar -->
        <div class="hero-accent" :class="profile.gender === 'female' ? 'hero-accent-female' : 'hero-accent-male'" />

        <v-row no-gutters>
          <!-- Photo column -->
          <v-col cols="12" sm="4" md="3">
            <div class="hero-photo-wrap">
              <v-img
                v-if="heroPhotoUrl"
                :src="heroPhotoUrl"
                cover
                position="top center"
                class="hero-photo"
              />
              <div v-else class="hero-photo-placeholder d-flex flex-column align-center justify-center">
                <v-icon size="88" :color="profile.gender === 'female' ? 'pink-lighten-3' : 'blue-lighten-3'">
                  mdi-account-circle
                </v-icon>
                <span v-if="!canViewPhotos" class="text-caption text-medium-emphasis mt-2">Photo is private</span>
              </div>
            </div>
          </v-col>

          <!-- Info column -->
          <v-col cols="12" sm="8" md="9" class="pa-5 pa-md-7 d-flex flex-column justify-center">
            <!-- Name + status + admin toggle -->
            <div class="d-flex align-center ga-2 flex-wrap mb-1">
              <h2 class="text-h5 font-weight-bold">
                {{ profile.full_name || (profile.gender === 'male' ? 'Groom Profile' : 'Bride Profile') }}
              </h2>
              <v-chip
                :color="profile.status === 'active' ? 'success' : profile.status === 'suspended' ? 'error' : profile.status === 'matched' ? 'pink' : 'warning'"
                size="small" variant="flat"
              >
                {{ profile.status === 'matched' ? 'Married' : profile.status }}
              </v-chip>
              <v-switch
                v-if="(auth.isAdmin || auth.isSuperAdmin) && profile.status !== 'matched'"
                :model-value="profile.status === 'active'"
                color="success" density="compact" hide-details
                :loading="togglingStatus" class="ml-1 flex-grow-0"
                @update:model-value="(val: boolean | null) => toggleStatus(val ?? false)"
              />
            </div>

            <!-- Sub-headline -->
            <p class="text-body-1 text-medium-emphasis mb-4">
              {{ ageLabel }}
              <span v-if="profile.profession"> · {{ profile.profession }}</span>
              <span v-if="profile.city"> · {{ profile.city }}<span v-if="profile.state">, {{ profile.state }}</span></span>
            </p>

            <!-- Stats chips grid -->
            <div class="hero-stats-grid mb-4">
              <div v-for="s in heroStats" :key="s.label" class="hero-stat-pill">
                <span class="hero-stat-label">{{ s.label }}</span>
                <span class="hero-stat-value">{{ s.value || '—' }}</span>
              </div>
            </div>

            <!-- Horoscope quick badges (if visible) -->
            <div
              v-if="(canBypassPrivacy || profile.birth_visible) && (profile.rashi || profile.star || profile.dhosam)"
              class="d-flex flex-wrap ga-2"
            >
              <v-chip v-if="profile.rashi" size="small" color="deep-purple" variant="tonal" prepend-icon="mdi-zodiac-aries">
                {{ fmtLabel(profile.rashi) }}
              </v-chip>
              <v-chip v-if="profile.star" size="small" color="indigo" variant="tonal" prepend-icon="mdi-star-four-points">
                {{ fmtLabel(profile.star) }}
              </v-chip>
              <v-chip
                v-if="profile.dhosam"
                size="small"
                :color="profile.dhosam === 'none' ? 'success' : 'orange-darken-1'"
                variant="tonal"
                prepend-icon="mdi-alert-circle-outline"
              >
                {{ fmtLabel(profile.dhosam) }}
              </v-chip>
            </div>
          </v-col>
        </v-row>
      </v-card>

      <!-- ── Admin actions ───────────────────────────────────────────────── -->
      <v-card v-if="(auth.isAdmin || auth.isSuperAdmin) && profile.status !== 'matched'" rounded="xl" class="mb-5 pa-4">
        <div class="d-flex align-center ga-3 flex-wrap">
          <v-icon color="medium-emphasis">mdi-shield-account</v-icon>
          <span class="text-body-2 text-medium-emphasis">Admin Actions</span>
          <v-spacer />
          <v-btn
            color="pink"
            variant="tonal"
            prepend-icon="mdi-heart-multiple"
            size="small"
            :loading="markingMarried"
            @click="markAsMarried"
          >
            Mark as Married
          </v-btn>
          <v-btn
            color="error"
            variant="tonal"
            prepend-icon="mdi-delete"
            size="small"
            :loading="deletingProfile"
            @click="confirmDelete"
          >
            Delete Profile
          </v-btn>
        </div>
      </v-card>
      <v-alert v-else-if="(auth.isAdmin || auth.isSuperAdmin) && profile.status === 'matched'" type="success" variant="tonal" rounded="xl" class="mb-5">
        <div class="d-flex align-center ga-3 flex-wrap">
          <div>
            <strong>This member has been marked as married.</strong>
            Their profile is no longer visible to other members.
          </div>
          <v-spacer />
          <v-btn
            color="error"
            variant="tonal"
            prepend-icon="mdi-delete"
            size="small"
            :loading="deletingProfile"
            @click="confirmDelete"
          >
            Delete Profile
          </v-btn>
        </div>
      </v-alert>

      <!-- ── Sections ───────────────────────────────────────────────────── -->
      <v-expansion-panels v-model="openPanels" multiple variant="accordion" rounded="xl">

        <!-- 1. Personal -->
        <v-expansion-panel>
          <v-expansion-panel-title>
            <v-icon start color="primary">mdi-account</v-icon>
            <span class="font-weight-semibold">Personal Details</span>
            <v-chip v-if="!canBypassPrivacy && !profile.personal_visible" size="x-small" color="warning" class="ml-2">Private</v-chip>
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
            <v-icon start color="orange-darken-2">mdi-om</v-icon>
            <span class="font-weight-semibold">Religious &amp; Cultural</span>
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
            <v-icon start color="deep-purple">mdi-star-crescent</v-icon>
            <span class="font-weight-semibold">Birth &amp; Horoscope</span>
            <v-chip v-if="!canBypassPrivacy && !profile.birth_visible" size="x-small" color="warning" class="ml-2">Private</v-chip>
          </v-expansion-panel-title>
          <v-expansion-panel-text>
            <!-- Birth details — gated by birth_visible -->
            <v-alert v-if="!canBypassPrivacy && !profile.birth_visible" type="warning" variant="tonal" density="compact" class="mb-4">
              Birth details are kept private by this member.
            </v-alert>
            <div v-else class="detail-grid">
              <detail-cell v-for="r in birthRows" :key="r.label" :row="r" />
            </div>

            <!-- Horoscope — has its own visibility flag (independent of birth_visible) -->
            <v-divider class="my-4" />
            <div class="d-flex align-center ga-3">
              <v-icon color="medium-emphasis">mdi-file-document-outline</v-icon>
              <div>
                <p class="text-caption text-medium-emphasis mb-1">Horoscope</p>
                <template v-if="canBypassPrivacy || profile.horoscope_visible">
                  <template v-if="profile.horoscope_key">
                    <!-- URL loaded → show open button -->
                    <v-btn
                      v-if="horoscopeUrl"
                      :href="horoscopeUrl"
                      target="_blank"
                      rel="noopener noreferrer"
                      prepend-icon="mdi-open-in-new"
                      color="primary"
                      variant="tonal"
                      size="small"
                    >
                      View / Download Horoscope
                    </v-btn>
                    <!-- Still fetching presigned URL -->
                    <div v-else class="d-flex align-center ga-2">
                      <v-progress-circular size="16" indeterminate color="primary" width="2" />
                      <span class="text-body-2 text-medium-emphasis">Loading horoscope link…</span>
                    </div>
                  </template>
                  <p v-else class="text-body-2 font-weight-medium mb-0">Not uploaded</p>
                </template>
                <p v-else class="text-body-2 font-italic text-medium-emphasis mb-0">Horoscope is kept private by this member.</p>
              </div>
            </div>
          </v-expansion-panel-text>
        </v-expansion-panel>

        <!-- 4. Professional -->
        <v-expansion-panel>
          <v-expansion-panel-title>
            <v-icon start color="teal">mdi-briefcase</v-icon>
            <span class="font-weight-semibold">Professional Details</span>
            <v-chip v-if="!canBypassPrivacy && !profile.professional_visible" size="x-small" color="warning" class="ml-2">Private</v-chip>
          </v-expansion-panel-title>
          <v-expansion-panel-text>
            <v-alert v-if="!canBypassPrivacy && !profile.professional_visible" type="warning" variant="tonal" density="compact" class="mb-4">
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
            <v-icon start color="blue-darken-2">mdi-map-marker</v-icon>
            <span class="font-weight-semibold">Location</span>
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
            <v-icon start color="orange-darken-2">mdi-home-heart</v-icon>
            <span class="font-weight-semibold">Family Details</span>
            <v-chip v-if="!canBypassPrivacy && !profile.family_visible" size="x-small" color="warning" class="ml-2">Private</v-chip>
          </v-expansion-panel-title>
          <v-expansion-panel-text>
            <v-alert v-if="!canBypassPrivacy && !profile.family_visible" type="warning" variant="tonal" density="compact" class="mb-4">
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
            <v-icon start color="green-darken-1">mdi-phone</v-icon>
            <span class="font-weight-semibold">Contact Details</span>
            <v-chip v-if="!canBypassPrivacy && !profile.contact_visible" size="x-small" color="warning" class="ml-2">Private</v-chip>
          </v-expansion-panel-title>
          <v-expansion-panel-text>
            <v-alert v-if="!canBypassPrivacy && !profile.contact_visible" type="warning" variant="tonal" density="compact" class="mb-4">
              Contact details are kept private by this member.
            </v-alert>
            <template v-else>
              <div class="d-flex flex-wrap ga-3">
                <v-btn
                  v-if="profile.mobile"
                  :href="`tel:${profile.mobile}`"
                  color="primary" variant="tonal" rounded="pill" size="small"
                  prepend-icon="mdi-phone"
                >
                  {{ profile.mobile }}
                </v-btn>
                <v-btn
                  v-if="profile.whatsapp"
                  :href="`https://wa.me/${profile.whatsapp?.replace(/[^0-9]/g,'')}`"
                  target="_blank" rel="noopener"
                  color="success" variant="tonal" rounded="pill" size="small"
                  prepend-icon="mdi-whatsapp"
                >
                  {{ profile.whatsapp }}
                </v-btn>
                <p v-if="!profile.mobile && !profile.whatsapp" class="text-body-2 text-medium-emphasis font-italic mb-0">No contact details added.</p>
              </div>
            </template>
          </v-expansion-panel-text>
        </v-expansion-panel>

        <!-- 8. Partner Preferences -->
        <v-expansion-panel>
          <v-expansion-panel-title>
            <v-icon start color="pink-darken-1">mdi-heart-search</v-icon>
            <span class="font-weight-semibold">Partner Preferences</span>
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

        <!-- 9. Photos -->
        <v-expansion-panel>
          <v-expansion-panel-title>
            <v-icon start color="pink-darken-2">mdi-image-multiple</v-icon>
            <span class="font-weight-semibold">Photos</span>
            <v-chip v-if="!canBypassPrivacy && !profile.photo_visible" size="x-small" color="warning" class="ml-2">Private</v-chip>
          </v-expansion-panel-title>
          <v-expansion-panel-text>
            <v-alert
              v-if="!canViewPhotos"
              type="warning"
              variant="tonal"
              density="compact"
            >
              Photos are kept private by this member.
            </v-alert>
            <p v-else-if="!profile.photo_keys?.length" class="text-body-2 text-medium-emphasis font-italic">
              No photos uploaded.
            </p>
            <v-row v-else dense>
              <v-col
                v-for="key in profile.photo_keys"
                :key="key"
                cols="6"
                sm="4"
                md="3"
              >
                <div style="aspect-ratio:3/4;overflow:hidden;border-radius:8px;background:#e0e0e0">
                  <v-img
                    v-if="detailPhotoUrls[key]"
                    :src="detailPhotoUrls[key]"
                    height="100%"
                    cover
                    position="top center"
                  />
                  <div
                    v-else
                    class="d-flex align-center justify-center"
                    style="height:100%"
                  >
                    <v-progress-circular indeterminate size="24" color="grey" />
                  </div>
                </div>
              </v-col>
            </v-row>
          </v-expansion-panel-text>
        </v-expansion-panel>

      </v-expansion-panels>
    </template>

    <!-- ── Mark Married Confirmation Dialog ────────────────────────────── -->
    <v-dialog v-model="marriedDialogOpen" max-width="480" persistent>
      <v-card rounded="xl">
        <v-card-title class="d-flex align-center pa-4">
          <v-icon color="pink" class="mr-2">mdi-heart-multiple</v-icon>
          Mark as Married
        </v-card-title>
        <v-divider />
        <v-card-text class="pa-4">
          <p class="text-body-2 text-medium-emphasis mb-3">
            Are you sure you want to mark <strong>{{ profile?.full_name || 'this member' }}</strong> as married?
          </p>
          <v-alert type="info" variant="tonal" density="compact" class="mb-0">
            Their profile will be <strong>hidden</strong> from all other members immediately.
            You can still delete it later if needed.
          </v-alert>
        </v-card-text>
        <v-divider />
        <v-card-actions class="pa-4">
          <v-btn variant="text" @click="marriedDialogOpen = false">Cancel</v-btn>
          <v-spacer />
          <v-btn
            color="pink"
            variant="elevated"
            prepend-icon="mdi-heart-multiple"
            :loading="markingMarried"
            @click="executeMarkMarried"
          >
            Confirm
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- ── Delete Profile Confirmation Dialog ─────────────────────────── -->
    <v-dialog v-model="deleteDialogOpen" max-width="480" persistent>
      <v-card rounded="xl">
        <v-card-title class="d-flex align-center pa-4">
          <v-icon color="error" class="mr-2">mdi-delete-alert</v-icon>
          Delete Profile
        </v-card-title>
        <v-divider />
        <v-card-text class="pa-4">
          <p class="text-body-2 text-medium-emphasis mb-3">
            Are you sure you want to permanently delete <strong>{{ profile?.full_name || 'this' }}</strong>'s profile?
          </p>
          <v-alert type="error" variant="tonal" density="compact" class="mb-0">
            This action <strong>cannot be undone</strong>. All profile data, photos,
            shortlists, and partner preferences will be permanently removed.
          </v-alert>
        </v-card-text>
        <v-divider />
        <v-card-actions class="pa-4">
          <v-btn variant="text" @click="deleteDialogOpen = false">Cancel</v-btn>
          <v-spacer />
          <v-btn
            color="error"
            variant="elevated"
            prepend-icon="mdi-delete"
            :loading="deletingProfile"
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
import { computed, defineComponent, h, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useQuery, useQueryClient } from '@tanstack/vue-query'
import { profilesApi, preferencesApi, filesApi } from '@/api/profiles'
import { useAuthStore } from '@/stores/auth'

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
const auth = useAuthStore()
const queryClient = useQueryClient()

// Open Personal Details panel by default
const openPanels = ref<number[]>([0])

// ── Admin: toggle profile status ─────────────────────────────────────────
const togglingStatus = ref(false)
async function toggleStatus(activate: boolean) {
  if (!profile.value) return
  togglingStatus.value = true
  try {
    await profilesApi.setStatus(profile.value.id, activate ? 'active' : 'suspended')
    queryClient.invalidateQueries({ queryKey: ['profile', props.id] })
  } catch {
    // ignore
  } finally {
    togglingStatus.value = false
  }
}

const markingMarried = ref(false)
const marriedDialogOpen = ref(false)
function markAsMarried() {
  marriedDialogOpen.value = true
}
async function executeMarkMarried() {
  if (!profile.value) return
  markingMarried.value = true
  try {
    await profilesApi.setStatus(profile.value.id, 'matched')
    queryClient.invalidateQueries({ queryKey: ['profile', props.id] })
  } catch {
    // ignore
  } finally {
    markingMarried.value = false
    marriedDialogOpen.value = false
  }
}

const deletingProfile = ref(false)
const deleteDialogOpen = ref(false)
function confirmDelete() {
  deleteDialogOpen.value = true
}
async function executeDeleteProfile() {
  if (!profile.value) return
  deletingProfile.value = true
  try {
    await profilesApi.delete(profile.value.id)
    router.push('/dashboard')
  } catch {
    // ignore
  } finally {
    deletingProfile.value = false
    deleteDialogOpen.value = false
  }
}

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

// ── Profile photos (presigned GET URLs for every key the viewer may see) ────────
// Map of S3 key → presigned URL.  Populated for the hero card and the Photos panel.
const detailPhotoUrls = reactive<Record<string, string>>({})

// True when the current viewer is allowed to see this profile's photos at all.
const canViewPhotos = ref(false)

// Presigned GET URL for the horoscope document (PDF or image). null = not accessible or not uploaded.
const horoscopeUrl = ref<string | null>(null)

// Admins, super-admins and the profile owner bypass ALL visibility flags.
// Members who have an accepted shortlist connection also bypass privacy.
const canBypassPrivacy = computed(() => {
  if (!profile.value) return false
  return (
    auth.isAdmin ||
    auth.isSuperAdmin ||
    auth.user?.id === profile.value.user_id ||
    profile.value.connection_status === 'accepted'
  )
})

// Convenience: the presigned URL for the first photo (used in the hero card).
const heroPhotoUrl = computed<string | null>(() => {
  const firstKey = profile.value?.photo_keys?.[0]
  return firstKey ? (detailPhotoUrls[firstKey] ?? null) : null
})

// Watch BOTH profile data AND auth.user so the block re-runs after fetchMe()
// resolves. Without this, the watch fires (immediate) before the auth store
// has populated user, isAdmin evaluates to false, and presigned URLs are never
// fetched for admin/owner viewers.
watch(
  [() => profile.value, () => auth.user],
  async ([p]) => {
    // Reset on every run so stale URLs from a previous profile don't linger.
    Object.keys(detailPhotoUrls).forEach((k) => delete detailPhotoUrls[k])
    canViewPhotos.value = false
    horoscopeUrl.value = null
    if (!p) return
    const isOwner = auth.user?.id === p.user_id
    const isConnected = p.connection_status === 'accepted'

    // Photos — respect photo_visible (bypassed for admin / owner / accepted connection).
    const canViewPhoto = auth.isAdmin || auth.isSuperAdmin || isOwner || isConnected || p.photo_visible
    canViewPhotos.value = canViewPhoto
    if (canViewPhoto && p.photo_keys?.length) {
      await Promise.allSettled(
        p.photo_keys.map(async (key) => {
          try {
            const { url } = await filesApi.presignGet(key)
            detailPhotoUrls[key] = url
          } catch {
            // leave entry absent → spinner stays visible
          }
        }),
      )
    }

    // Horoscope — uses its own horoscope_visible flag (independent of birth_visible).
    const canViewHoroscope = auth.isAdmin || auth.isSuperAdmin || isOwner || isConnected || p.horoscope_visible
    if (canViewHoroscope && p.horoscope_key) {
      try {
        const { url } = await filesApi.presignGet(p.horoscope_key)
        horoscopeUrl.value = url
      } catch {
        // presign failed – URL stays null
      }
    }
  },
  { immediate: true },
)

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

// ── Age (calculated from date_of_birth only) ─────────────────────────────────
const ageLabel = computed(() => {
  const dob = profile.value?.date_of_birth
  if (!dob) return '—'
  const d = new Date(dob)
  const t = new Date()
  let age = t.getFullYear() - d.getFullYear()
  if (t.getMonth() < d.getMonth() || (t.getMonth() === d.getMonth() && t.getDate() < d.getDate())) age--
  // Guard: only show if within plausible matrimonial range
  if (age < 18 || age > 80) return '—'
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
    { label: 'Manglik', value: p.dhosam ? (p.dhosam === 'chevvai' ? 'Yes' : 'No') : null },
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
/* ── Detail grid ──────────────────────────────────────────────────── */
.detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(190px, 1fr));
  gap: 16px 24px;
}
.detail-cell { min-width: 0; }

/* ── Hero card ────────────────────────────────────────────────────── */
.hero-accent {
  height: 5px;
  border-radius: 12px 12px 0 0;
}
.hero-accent-female {
  background: linear-gradient(90deg, #E91E63, #F06292, #CE93D8);
}
.hero-accent-male {
  background: linear-gradient(90deg, #1E88E5, #42A5F5, #7B1FA2);
}

.hero-photo-wrap {
  height: 280px;
  overflow: hidden;
  position: relative;
  background: #f3f4f6;
}
.hero-photo {
  width: 100%;
  height: 280px;
}
.hero-photo-placeholder {
  height: 280px;
  background: linear-gradient(160deg, #f8f7ff 0%, #f0eeff 100%);
}

/* ── Stats chips ──────────────────────────────────────────────────── */
.hero-stats-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.hero-stat-pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(30, 136, 229, 0.07);
  border: 1px solid rgba(30, 136, 229, 0.15);
  font-size: 0.78rem;
}
.hero-stat-label {
  color: #888;
  font-weight: 500;
}
.hero-stat-label::after { content: ':'; }
.hero-stat-value {
  font-weight: 600;
  color: #333;
}
</style>
