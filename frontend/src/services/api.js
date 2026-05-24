import axios from 'axios'

const BASE_URL = 'http://localhost:8000/api/v1'

const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const stored = localStorage.getItem('auth-storage')
  if (stored) {
    try {
      const parsed = JSON.parse(stored)
      const token = parsed?.state?.token
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
    } catch (_) {}
  }
  return config
})

api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth-storage')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// ─── Auth ───────────────────────────────────────────────────────────────────
export const login = (email, password) =>
  api.post('/auth/login', { email, password })

// ─── Rooms ──────────────────────────────────────────────────────────────────
export const getRooms = () => api.get('/rooms')
export const getRoom = (id) => api.get(`/rooms/${id}`)

// ─── Devices ────────────────────────────────────────────────────────────────
export const getDevices = (params) => api.get('/devices', { params })
export const controlDevice = (id, payload) =>
  api.post(`/devices/${id}/control`, payload)

// ─── Sensors ────────────────────────────────────────────────────────────────
export const getSensors = () => api.get('/sensors')
export const getSensorData = (id, period = '1h') =>
  api.get(`/sensors/${id}/data`, { params: { period } })

// ─── Alerts ─────────────────────────────────────────────────────────────────
export const getAlerts = (params) => api.get('/alerts', { params })
export const getAlertsHistory = () => api.get('/alerts/history')
export const acknowledgeAlert = (id) => api.post(`/alerts/${id}/acknowledge`)
export const resolveAlert = (id) => api.post(`/alerts/${id}/resolve`)

// ─── Consumption ────────────────────────────────────────────────────────────
export const getConsumption = (period = '24h') =>
  api.get('/consumption', { params: { period } })

// ─── Predictions ────────────────────────────────────────────────────────────
export const getPredictions24h = () => api.get('/predictions/24h')

export default api
