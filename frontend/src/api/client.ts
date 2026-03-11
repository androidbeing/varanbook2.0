import axios from 'axios'

// If VITE_API_BASE_URL is set explicitly in .env, use it.
// Otherwise derive the API origin from the current page's hostname so that
// LAN access (e.g. http://192.168.x.x:5173) automatically points to the
// backend on port 8000 of the same host.
const BASE_URL =
  import.meta.env.VITE_API_BASE_URL ??
  `${window.location.protocol}//${window.location.hostname}:8000`

const client = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
})

// Attach JWT on every request and forward the tenant ID header so the
// backend middleware can resolve the tenant even on localhost (no subdomain).
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`

    // Decode the JWT payload (no signature verification needed client-side)
    // and forward the tenant id as X-Tenant-ID so TenantMiddleware can resolve
    // the tenant when running on localhost without a subdomain.
    try {
      const payloadB64 = token.split('.')[1]
      if (payloadB64) {
        const payload = JSON.parse(atob(payloadB64.replace(/-/g, '+').replace(/_/g, '/')))
        if (payload.tid) {
          config.headers['X-Tenant-ID'] = payload.tid
        }
      }
    } catch {
      // Malformed token – skip header injection; auth will fail normally
    }
  }
  return config
})

// Token refresh logic with request queuing to handle concurrent 401s.
// While a refresh is in flight, subsequent 401 failures are queued and
// resolved/rejected once the refresh completes instead of each triggering
// their own refresh attempt.
let isRefreshing = false
let refreshQueue: Array<{ resolve: (token: string) => void; reject: (err: unknown) => void }> = []

function drainQueue(token: string) {
  refreshQueue.forEach((p) => p.resolve(token))
  refreshQueue = []
}

function rejectQueue(err: unknown) {
  refreshQueue.forEach((p) => p.reject(err))
  refreshQueue = []
}

function clearSession() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  window.location.href = '/login'
}

// 401 → attempt silent token refresh, then retry the original request.
// Exceptions: login and refresh endpoints themselves are passed through.
client.interceptors.response.use(
  (res) => res,
  async (err) => {
    const originalConfig = err.config
    const url: string = originalConfig?.url ?? ''

    // Pass through errors from auth endpoints to avoid infinite loops
    if (
      err.response?.status !== 401 ||
      url.includes('/auth/login') ||
      url.includes('/auth/refresh') ||
      originalConfig?._retry
    ) {
      return Promise.reject(err)
    }

    originalConfig._retry = true

    if (isRefreshing) {
      // Another refresh is already in flight — queue this request
      return new Promise<string>((resolve, reject) => {
        refreshQueue.push({ resolve, reject })
      })
        .then((newToken) => {
          originalConfig.headers.Authorization = `Bearer ${newToken}`
          return client(originalConfig)
        })
        .catch(() => Promise.reject(err))
    }

    const storedRefreshToken = localStorage.getItem('refresh_token')
    if (!storedRefreshToken) {
      clearSession()
      return Promise.reject(err)
    }

    isRefreshing = true
    try {
      // Call refresh directly via axios to avoid going through this interceptor
      const response = await axios.post<{ access_token: string; refresh_token?: string }>(
        `${BASE_URL}/auth/refresh`,
        { refresh_token: storedRefreshToken },
        { headers: { 'Content-Type': 'application/json' } },
      )
      const { access_token, refresh_token } = response.data

      localStorage.setItem('access_token', access_token)
      if (refresh_token) {
        localStorage.setItem('refresh_token', refresh_token)
      }

      // Update the shared client default so future requests use the new token
      client.defaults.headers.common.Authorization = `Bearer ${access_token}`

      drainQueue(access_token)
      originalConfig.headers.Authorization = `Bearer ${access_token}`
      return client(originalConfig)
    } catch (refreshErr) {
      rejectQueue(refreshErr)
      clearSession()
      return Promise.reject(refreshErr)
    } finally {
      isRefreshing = false
    }
  },
)

export default client
