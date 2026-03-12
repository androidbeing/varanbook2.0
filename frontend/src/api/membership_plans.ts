import client from './client'
import type { TenantPlan, Subscription, PaginatedResponse } from '@/types'

export interface SubscriptionsQuery {
  status?: string
  user_id?: string
  search?: string
  page?: number
  size?: number
}

export interface CreateSubscriptionPayload {
  user_id: string
  plan_template_id: string
  starts_at?: string
  notes?: string
}

export const membershipApi = {
  /** List effective membership plans available to this tenant. */
  listPlans(): Promise<TenantPlan[]> {
    return client.get('/plans').then((r) => r.data)
  },

  /** Return the authenticated member's current active subscription, or null. */
  mySubscription(): Promise<Subscription | null> {
    return client.get('/subscriptions/me').then((r) => r.data)
  },

  /** Admin: paginated list of subscriptions in this tenant. */
  listSubscriptions(
    params: SubscriptionsQuery = {},
  ): Promise<PaginatedResponse<Subscription>> {
    return client.get('/subscriptions', { params }).then((r) => r.data)
  },

  /** Admin: assign a plan to a member, creating a new subscription. */
  createSubscription(data: CreateSubscriptionPayload): Promise<Subscription> {
    return client.post('/subscriptions', data).then((r) => r.data)
  },

  /** Admin: cancel an existing subscription. */
  cancelSubscription(id: string): Promise<Subscription> {
    return client.patch(`/subscriptions/${id}`, { status: 'cancelled' }).then((r) => r.data)
  },
}
