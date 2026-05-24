import { create } from 'zustand'
import { persist } from 'zustand/middleware'

const useAuthStore = create(
  persist(
    (set, get) => ({
      token: null,
      refreshToken: null,
      user: null,

      setAuth: (accessToken, refreshToken, user) => {
        set({ token: accessToken, refreshToken, user })
      },

      logout: () => {
        set({ token: null, refreshToken: null, user: null })
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
      }),
    }
  )
)

export default useAuthStore
