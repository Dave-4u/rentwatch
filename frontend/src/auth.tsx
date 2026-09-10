import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { api, type User } from './api/client'

interface AuthState {
  user: User | null
  token: string | null
  loading: boolean
  login: (email: string, password: string) => Promise<User>
  logout: () => void
  refresh: () => Promise<void>
  setSession: (token: string, user: User) => void
}

const AuthCtx = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(localStorage.getItem('rw_token'))
  const [loading, setLoading] = useState(true)

  const setSession = useCallback((t: string, u: User) => {
    localStorage.setItem('rw_token', t)
    localStorage.setItem('rw_user', JSON.stringify(u))
    setToken(t)
    setUser(u)
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('rw_token')
    localStorage.removeItem('rw_user')
    setToken(null)
    setUser(null)
  }, [])

  const refresh = useCallback(async () => {
    if (!localStorage.getItem('rw_token')) {
      setLoading(false)
      return
    }
    try {
      const me = await api.me()
      setUser(me)
      localStorage.setItem('rw_user', JSON.stringify(me))
    } catch {
      logout()
    } finally {
      setLoading(false)
    }
  }, [logout])

  useEffect(() => {
    refresh()
  }, [refresh])

  const login = useCallback(
    async (email: string, password: string) => {
      const res = await api.login(email, password)
      setSession(res.access_token, res.user)
      return res.user
    },
    [setSession],
  )

  const value = useMemo(
    () => ({ user, token, loading, login, logout, refresh, setSession }),
    [user, token, loading, login, logout, refresh, setSession],
  )

  return <AuthCtx.Provider value={value}>{children}</AuthCtx.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthCtx)
  if (!ctx) throw new Error('useAuth outside provider')
  return ctx
}
