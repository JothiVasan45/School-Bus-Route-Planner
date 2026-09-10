import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import api from '../api/client'

interface AuthState {
  token: string | null
  role: string | null
  username: string | null
  fullName: string | null
  login: (username: string, password: string) => Promise<void>
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      role: null,
      username: null,
      fullName: null,

      login: async (username: string, password: string) => {
        const formData = new FormData()
        formData.append('username', username)
        formData.append('password', password)
        const res = await api.post('/auth/token', formData, {
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        })
        set({
          token: res.data.access_token,
          role: res.data.role,
          username: res.data.username,
          fullName: res.data.full_name,
        })
        api.defaults.headers.common['Authorization'] = `Bearer ${res.data.access_token}`
      },

      logout: () => {
        set({ token: null, role: null, username: null, fullName: null })
        delete api.defaults.headers.common['Authorization']
      },
    }),
    { name: 'auth-store' }
  )
)

// Rehydrate token on page load
const stored = useAuthStore.getState()
if (stored.token) {
  api.defaults.headers.common['Authorization'] = `Bearer ${stored.token}`
}
