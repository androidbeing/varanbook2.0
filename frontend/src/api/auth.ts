import client from './client'
import type { AuthTokens, LoginPayload } from '@/types'

export const authApi = {
  login(payload: LoginPayload): Promise<AuthTokens> {
    return client.post('/auth/login', payload).then((r) => r.data)
  },

  refresh(refreshToken: string): Promise<AuthTokens> {
    return client
      .post('/auth/refresh', { refresh_token: refreshToken })
      .then((r) => r.data)
  },

  logout(): Promise<void> {
    return client.post('/auth/logout').then(() => undefined)
  },

  me(): Promise<import('@/types').User> {
    return client.get('/users/me').then((r) => r.data)
  },

  requestPasswordReset(email: string): Promise<void> {
    return client.post('/auth/password-reset/request', { email }).then(() => undefined)
  },

  confirmPasswordReset(token: string, newPassword: string): Promise<void> {
    return client
      .post('/auth/password-reset/confirm', { token, new_password: newPassword })
      .then(() => undefined)
  },
}
