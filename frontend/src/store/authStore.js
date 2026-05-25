import { create } from 'zustand'
import { persist } from 'zustand/middleware'

function decodeJwtPayload(token) {
  try {
    const payload = token.split('.')[1]
    const decoded = JSON.parse(atob(payload.replace(/-/g, '+').replace(/_/g, '/')))
    return decoded
  } catch {
    return {}
  }
}

const useAuthStore = create(
  persist(
    (set, get) => ({
      token: null,
      refreshToken: null,
      user: null,
      role: null,

      setAuth: (accessToken, refreshToken, user) => {
        const payload = decodeJwtPayload(accessToken)
        const role = payload.role || user?.role || 'viewer'
        set({ token: accessToken, refreshToken, user: { ...user }, role })
      },

      isAdmin: () => get().role === 'admin',
      isOperador: () => get().role === 'admin' || get().role === 'operador',

      logout: () => {
        set({ token: null, refreshToken: null, user: null, role: null })
        localStorage.removeItem('auth-storage')
      },

      isAuthenticated: () => {
        return !!get().token
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        token: state.token,
        refreshToken: state.refreshToken,
        user: state.user,
        role: state.role,
      }),
    }
  )
)

export default useAuthStore
