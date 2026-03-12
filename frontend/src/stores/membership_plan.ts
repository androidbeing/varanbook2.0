import { ref } from 'vue'
import { defineStore } from 'pinia'
import { membershipApi } from '@/api/membership_plans'
import type { TenantPlan, Subscription } from '@/types'

export const useMembershipStore = defineStore('membership', () => {
  const plans = ref<TenantPlan[]>([])
  const mySubscription = ref<Subscription | null>(null)
  const loadingPlans = ref(false)
  const loadingSubscription = ref(false)

  async function fetchPlans() {
    loadingPlans.value = true
    try {
      plans.value = await membershipApi.listPlans()
    } finally {
      loadingPlans.value = false
    }
  }

  async function fetchMySubscription() {
    loadingSubscription.value = true
    try {
      mySubscription.value = await membershipApi.mySubscription()
    } finally {
      loadingSubscription.value = false
    }
  }

  function reset() {
    plans.value = []
    mySubscription.value = null
  }

  return {
    plans,
    mySubscription,
    loadingPlans,
    loadingSubscription,
    fetchPlans,
    fetchMySubscription,
    reset,
  }
})
