import axios from 'axios'

// Caminho RELATIVO por padrão: as chamadas vão para o mesmo host que serviu o
// app (localhost, IP da rede ou link do ngrok), e o nginx/Vite faz proxy de
// /api → backend:8000. Isso permite acessar de um tablet/celular via ngrok sem
// recompilar. Defina VITE_API_URL apenas se quiser apontar para outra origem.
const BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'

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
export const createRoom = (payload) => api.post('/rooms', payload)
export const deleteRoom = (id) => api.delete(`/rooms/${id}`)

// ─── Devices ────────────────────────────────────────────────────────────────
export const getDevices = (params) => api.get('/devices', { params })
export const createDevice = (payload) => api.post('/devices', payload)
export const updateDevice = (id, payload) => api.patch(`/devices/${id}`, payload)
export const deleteDevice = (id) => api.delete(`/devices/${id}`)
export const controlDevice = (id, payload) =>
  api.post(`/devices/${id}/control`, payload)

// ─── Sensors ────────────────────────────────────────────────────────────────
export const getSensors = () => api.get('/sensors')
export const getSensorData = (id, period = '1h') =>
  api.get(`/sensors/${id}/data`, { params: { period } })
export const getSensorLatest = (id) => api.get(`/sensors/${id}/latest`)

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
// export const getPredictions24h = () => api.get('/api/v1/predictions/24h');
export const trainModel = () => api.post('/predictions/train')

// ─── Users ──────────────────────────────────────────────────────────────────
export const getUsers = (params) => api.get('/users', { params })
export const createUser = (payload) => api.post('/users', payload)
export const updateUser = (id, payload) => api.patch(`/users/${id}`, payload)
export const deleteUser = (id) => api.delete(`/users/${id}`)

// ─── Health / System Status ──────────────────────────────────────────────────
export const getHealth = () => api.get('/health')

export default api
