import { useState, useEffect, useCallback, createContext, useContext } from 'react'
import api from '../api'

export interface AuthUser {
  id: number
  email: string | null
  phone: string | null
  full_name: string | null
  is_admin: boolean
}

interface AuthContextType {
  token: string | null
  user: AuthUser | null
  login: (email: string, password: string) => Promise<AuthUser>
  googleLogin: (credential: string) => Promise<AuthUser>
  logout: () => void
  isLoggedIn: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('ticketly_token'))
  const [user, setUser] = useState<AuthUser | null>(() => {
    try { return JSON.parse(localStorage.getItem('ticketly_user') || 'null') } catch { return null }
  })

  const login = useCallback(async (email: string, password: string) => {
    const form = new URLSearchParams()
    form.append('username', email)
    form.append('password', password)
    const res = await api.post('/auth/token', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    const tok: string = res.data.access_token
    localStorage.setItem('ticketly_token', tok)
    setToken(tok)
    const meRes = await api.get('/auth/me', { headers: { Authorization: `Bearer ${tok}` } })
    localStorage.setItem('ticketly_user', JSON.stringify(meRes.data))
    setUser(meRes.data)
    return meRes.data as AuthUser
  }, [])

  const googleLogin = useCallback(async (credential: string) => {
    const res = await api.post('/auth/google', { token: credential })
    const tok: string = res.data.access_token
    localStorage.setItem('ticketly_token', tok)
    setToken(tok)
    const meRes = await api.get('/auth/me', { headers: { Authorization: `Bearer ${tok}` } })
    localStorage.setItem('ticketly_user', JSON.stringify(meRes.data))
    setUser(meRes.data)
    return meRes.data as AuthUser
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('ticketly_token')
    localStorage.removeItem('ticketly_user')
    setToken(null)
    setUser(null)
  }, [])

  useEffect(() => {
    const handler = () => logout()
    window.addEventListener('ticketly:logout', handler)
    return () => window.removeEventListener('ticketly:logout', handler)
  }, [logout])

  return (
    <AuthContext.Provider value={{ token, user, login, googleLogin, logout, isLoggedIn: !!token }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
