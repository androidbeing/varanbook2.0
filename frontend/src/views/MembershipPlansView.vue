<template>
  <div>
    <!-- ── Header ─────────────────────────────────────────────────────────── -->
    <v-row class="mb-6">
      <v-col>
        <v-card color="primary" rounded="xl" class="pa-6">
          <div class="d-flex align-center ga-4">
            <v-icon size="48" class="opacity-75">mdi-card-account-details-star</v-icon>
            <div>
              <h1 class="text-h5 font-weight-bold">Membership</h1>
              <p class="text-body-2 opacity-80 mb-0">
                View your active plan and explore available memberships.
              </p>
            </div>
          </div>
        </v-card>
      </v-col>
    </v-row>

    <!-- ── Current Subscription ───────────────────────────────────────────── -->
    <v-row class="mb-4">
      <v-col cols="12">
        <h2 class="text-h6 font-weight-semibold mb-3">Your Subscription</h2>

        <v-skeleton-loader
          v-if="store.loadingSubscription"
          type="card"
          rounded="xl"
          class="mb-2"
        />

        <!-- Active Subscription Card -->
        <v-card
          v-else-if="store.mySubscription && store.mySubscription.status === 'active'"
          rounded="xl"
          color="success"
          variant="tonal"
          class="mb-2"
        >
          <v-card-text class="pa-5">
            <div class="d-flex align-center justify-space-between flex-wrap ga-3">
              <div>
                <div class="d-flex align-center ga-2 mb-1">
                  <v-icon color="success" size="22">mdi-check-decagram</v-icon>
                  <span class="text-subtitle-1 font-weight-bold">
                    {{ store.mySubscription.plan_name }}
                  </span>
                  <v-chip size="x-small" color="success" variant="flat">Active</v-chip>
                </div>
                <p v-if="store.mySubscription.plan_tagline" class="text-body-2 mb-1 opacity-80">
                  {{ store.mySubscription.plan_tagline }}
                </p>
                <p class="text-body-2 mb-0">
                  Valid until
                  <strong>{{ formatDate(store.mySubscription.expires_at) }}</strong>
                  &nbsp;·&nbsp;
                  <span :class="daysLeftClass">{{ daysLeft }} day{{ daysLeft !== 1 ? 's' : '' }} remaining</span>
                </p>
              </div>
              <div class="text-right">
                <div class="text-h5 font-weight-bold text-success">
                  ₹{{ Number(store.mySubscription.price_paid_inr).toLocaleString('en-IN') }}
                </div>
                <div class="text-caption opacity-70">
                  {{ store.mySubscription.duration_months }} month plan
                </div>
              </div>
            </div>
          </v-card-text>
        </v-card>

        <!-- No subscription -->
        <v-card v-else rounded="xl" variant="outlined" class="mb-2">
          <v-card-text class="pa-5 d-flex align-center ga-4">
            <v-icon size="40" color="warning">mdi-information-outline</v-icon>
            <div>
              <p class="text-subtitle-1 font-weight-semibold mb-0">No active subscription</p>
              <p class="text-body-2 text-medium-emphasis mb-0">
                Contact your matrimony centre to subscribe to a membership plan.
              </p>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- ── Payment Information ────────────────────────────────────────────── -->
    <v-row v-if="paymentInfo && hasPaymentInfo" class="mb-4">
      <v-col cols="12">
        <h2 class="text-h6 font-weight-semibold mb-3">Payment Information</h2>
        <v-card rounded="xl" variant="outlined">
          <v-card-text class="pa-5">
            <v-row align="center">
              <!-- QR Code -->
              <v-col v-if="qrUrl" cols="12" sm="4" md="3" class="text-center">
                <v-img :src="qrUrl" max-width="200" class="mx-auto rounded-lg" />
                <p class="text-caption text-medium-emphasis mt-2 mb-0">Scan to pay via UPI</p>
              </v-col>

              <!-- UPI Details -->
              <v-col cols="12" :sm="qrUrl ? 8 : 12" :md="qrUrl ? 5 : 8">
                <div class="mb-3" v-if="paymentInfo.upi_name">
                  <div class="text-caption text-medium-emphasis mb-1">UPI Account Name</div>
                  <div class="text-body-1 font-weight-semibold">{{ paymentInfo.upi_name }}</div>
                </div>
                <div class="mb-3" v-if="paymentInfo.upi_id">
                  <div class="text-caption text-medium-emphasis mb-1">UPI ID</div>
                  <div class="d-flex align-center ga-2">
                    <v-chip color="primary" variant="tonal" size="default" class="font-weight-medium">
                      {{ paymentInfo.upi_id }}
                    </v-chip>
                    <v-btn
                      icon
                      size="x-small"
                      variant="text"
                      @click="copyUpiId"
                    >
                      <v-icon size="16">mdi-content-copy</v-icon>
                      <v-tooltip activator="parent" location="top">Copy UPI ID</v-tooltip>
                    </v-btn>
                  </div>
                </div>
                <div v-if="paymentInfo.tenant_name" class="mb-3">
                  <div class="text-caption text-medium-emphasis mb-1">Pay To</div>
                  <div class="text-body-2">{{ paymentInfo.tenant_name }}</div>
                </div>
              </v-col>

              <!-- WhatsApp CTA -->
              <v-col v-if="paymentInfo.payment_whatsapp" cols="12" :sm="qrUrl ? 12 : 12" :md="qrUrl ? 4 : 4">
                <v-card color="green-lighten-5" rounded="lg" variant="flat">
                  <v-card-text class="pa-4 text-center">
                    <v-icon color="green" size="32" class="mb-2">mdi-whatsapp</v-icon>
                    <p class="text-body-2 mb-3">
                      After making payment, send a screenshot via WhatsApp for confirmation.
                    </p>
                    <v-btn
                      color="green"
                      variant="elevated"
                      prepend-icon="mdi-whatsapp"
                      :href="whatsappLink"
                      target="_blank"
                      block
                    >
                      Send Payment Screenshot
                    </v-btn>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- ── Available Plans ────────────────────────────────────────────────── -->
    <v-row class="mb-2">
      <v-col cols="12">
        <h2 class="text-h6 font-weight-semibold mb-1">Available Plans</h2>
        <p class="text-body-2 text-medium-emphasis mb-4">
          To subscribe or upgrade, reach out to your matrimony centre admin.
        </p>
      </v-col>
    </v-row>

    <v-row v-if="store.loadingPlans">
      <v-col v-for="n in 3" :key="n" cols="12" sm="6" md="4">
        <v-skeleton-loader type="card" rounded="xl" />
      </v-col>
    </v-row>

    <v-row v-else>
      <v-col
        v-for="plan in store.plans"
        :key="plan.id"
        cols="12"
        sm="6"
        md="4"
      >
        <v-card
          rounded="xl"
          :variant="isCurrentPlan(plan) ? 'flat' : 'outlined'"
          :color="isCurrentPlan(plan) ? 'primary' : undefined"
          :class="{ 'border-md border-primary': !isCurrentPlan(plan) && isPopular(plan) }"
          height="100%"
        >
          <!-- Popular badge -->
          <v-chip
            v-if="isPopular(plan)"
            color="orange"
            size="small"
            class="ma-3"
            style="position:absolute; top:0; right:0"
          >
            Popular
          </v-chip>

          <v-card-text class="pa-6">
            <!-- Plan name & tagline -->
            <div class="mb-4">
              <p class="text-overline mb-0 opacity-70">{{ plan.duration_months }} months</p>
              <h3 class="text-h5 font-weight-bold mb-1">{{ plan.name }}</h3>
              <p v-if="plan.tagline" class="text-body-2 mb-0 opacity-80">{{ plan.tagline }}</p>
            </div>

            <!-- Price -->
            <div class="mb-5">
              <span class="text-h4 font-weight-bold">
                ₹{{ Number(plan.effective_price_inr).toLocaleString('en-IN') }}
              </span>
              <span
                v-if="plan.has_override && plan.effective_price_inr !== plan.base_price_inr"
                class="text-body-2 text-decoration-line-through opacity-60 ml-2"
              >
                ₹{{ Number(plan.base_price_inr).toLocaleString('en-IN') }}
              </span>
            </div>

            <!-- Description -->
            <p v-if="plan.description" class="text-body-2 mb-4 opacity-80">{{ plan.description }}</p>

            <!-- Features -->
            <v-list v-if="plan.features?.length" density="compact" class="pa-0">
              <v-list-item
                v-for="(feature, i) in plan.features"
                :key="i"
                density="compact"
                class="px-0"
                min-height="28"
              >
                <template #prepend>
                  <v-icon size="16" color="success" class="mr-2">mdi-check-circle</v-icon>
                </template>
                <v-list-item-title class="text-body-2">{{ feature }}</v-list-item-title>
              </v-list-item>
            </v-list>

            <v-divider class="my-4" />

            <!-- CTA -->
            <v-chip
              v-if="isCurrentPlan(plan)"
              color="white"
              variant="flat"
              prepend-icon="mdi-check"
              block
              class="font-weight-semibold"
            >
              Your Current Plan
            </v-chip>
            <p v-else class="text-caption text-medium-emphasis text-center mb-0">
              Contact your centre to subscribe
            </p>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col v-if="!store.loadingPlans && store.plans.length === 0" cols="12">
        <v-card rounded="xl" variant="outlined">
          <v-card-text class="pa-6 text-center text-medium-emphasis">
            <v-icon size="48" class="mb-2">mdi-card-off-outline</v-icon>
            <p class="mb-0">No membership plans are available at this time.</p>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, onMounted } from 'vue'
import { useMembershipStore } from '@/stores/membership_plan'
import { membershipApi } from '@/api/membership_plans'
import { filesApi } from '@/api/profiles'
import type { TenantPlan, TenantPaymentInfo } from '@/types'

const store = useMembershipStore()

// ── Payment Info ──────────────────────────────────────────────────────────────
const paymentInfo = ref<TenantPaymentInfo | null>(null)
const qrUrl = ref<string | null>(null)

const hasPaymentInfo = computed(() => {
  if (!paymentInfo.value) return false
  return !!(paymentInfo.value.upi_id || paymentInfo.value.upi_name || paymentInfo.value.upi_qr_key || paymentInfo.value.payment_whatsapp)
})

const whatsappLink = computed(() => {
  if (!paymentInfo.value?.payment_whatsapp) return '#'
  const phone = paymentInfo.value.payment_whatsapp.replace('+', '')
  const text = encodeURIComponent('Hi, I have made a payment for my membership plan. Please find the screenshot attached.')
  return `https://wa.me/${phone}?text=${text}`
})

function copyUpiId() {
  if (paymentInfo.value?.upi_id) {
    navigator.clipboard.writeText(paymentInfo.value.upi_id)
  }
}

async function loadPaymentInfo() {
  try {
    paymentInfo.value = await membershipApi.getPaymentInfo()
    if (paymentInfo.value?.upi_qr_key) {
      try {
        const { url } = await filesApi.presignGet(paymentInfo.value.upi_qr_key)
        qrUrl.value = url
      } catch {
        // QR image may not be accessible
      }
    }
  } catch {
    // Payment info may not be configured
  }
}

onMounted(() => {
  store.fetchPlans()
  store.fetchMySubscription()
  loadPaymentInfo()
})

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  })
}

const daysLeft = computed(() => {
  if (!store.mySubscription) return 0
  const diff = new Date(store.mySubscription.expires_at).getTime() - Date.now()
  return Math.max(0, Math.ceil(diff / (1000 * 60 * 60 * 24)))
})

const daysLeftClass = computed(() => {
  if (daysLeft.value <= 7) return 'text-error font-weight-semibold'
  if (daysLeft.value <= 30) return 'text-warning font-weight-semibold'
  return 'text-success'
})

function isCurrentPlan(plan: TenantPlan): boolean {
  return store.mySubscription?.plan_template_id === plan.id &&
    store.mySubscription?.status === 'active'
}

function isPopular(plan: TenantPlan): boolean {
  return plan.duration_months === 6
}
</script>
