import client from './client'
import type { Tenant, TenantCreate, TenantUpdate, TenantList } from '@/types'

export interface AdminCreate {
  email: string
  password: string
  full_name: string
  phone?: string | null
  tenant_id: string
}

export const tenantApi = {
  list(page = 1, pageSize = 20, isActive?: boolean): Promise<TenantList> {
    const params: Record<string, unknown> = { page, page_size: pageSize }
    if (isActive !== undefined) params.is_active = isActive
    return client.get('/admin/tenants/', { params }).then((r) => r.data)
  },

  get(id: string): Promise<Tenant> {
    return client.get(`/admin/tenants/${id}`).then((r) => r.data)
  },

  create(payload: TenantCreate): Promise<Tenant> {
    return client.post('/admin/tenants/', payload).then((r) => r.data)
  },

  update(id: string, payload: TenantUpdate): Promise<Tenant> {
    return client.patch(`/admin/tenants/${id}`, payload).then((r) => r.data)
  },

  deactivate(id: string): Promise<void> {
    return client.delete(`/admin/tenants/${id}`).then(() => undefined)
  },

  createAdmin(payload: AdminCreate): Promise<{ id: string; email: string }> {
    return client.post('/users/admin', payload).then((r) => r.data)
  },
}
