import { ref } from 'vue'
import { defineStore } from 'pinia'
import { shortlistApi } from '@/api/shortlist'

/**
 * Tracks which profiles the current member has shortlisted.
 * Stores a Map of  to_profile_id → shortlist_entry_id  for O(1) lookups.
 */
export const useShortlistStore = defineStore('shortlist', () => {
  // Map of  to_profile_id → shortlist_entry_id
  const map = ref<Map<string, string>>(new Map())
  const initialized = ref(false)
  const loading = ref(false)

  function isShortlisted(profileId: string): boolean {
    return map.value.has(profileId)
  }

  /** Load all sent shortlist entries once per session. */
  async function init(): Promise<void> {
    if (initialized.value) return
    loading.value = true
    try {
      const list = await shortlistApi.sent(500)
      const m = new Map<string, string>()
      for (const entry of list.items) {
        m.set(entry.to_profile_id, entry.id)
      }
      map.value = m
      initialized.value = true
    } finally {
      loading.value = false
    }
  }

  /**
   * Toggle shortlist state for a profile.
   * Returns true if the profile is now shortlisted, false if removed.
   */
  async function toggle(profileId: string): Promise<boolean> {
    if (map.value.has(profileId)) {
      await shortlistApi.deleteByProfile(profileId)
      const m = new Map(map.value)
      m.delete(profileId)
      map.value = m
      return false
    } else {
      const entry = await shortlistApi.create(profileId)
      const m = new Map(map.value)
      m.set(profileId, entry.id)
      map.value = m
      return true
    }
  }

  /** Call on logout so the next user starts fresh. */
  function reset(): void {
    map.value = new Map()
    initialized.value = false
  }

  /** Manually remove a profileId from the local map (after an API delete). */
  function removeFromMap(profileId: string): void {
    const m = new Map(map.value)
    m.delete(profileId)
    map.value = m
  }

  return { isShortlisted, loading, initialized, init, toggle, reset, removeFromMap }
})
