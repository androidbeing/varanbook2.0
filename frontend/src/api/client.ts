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

// 401 → clear tokens and redirect to login
// Exception: skip redirect for the login endpoint itself (wrong credentials)
client.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401 && !err.config?.url?.includes('/auth/login')) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  },
)

export default client
