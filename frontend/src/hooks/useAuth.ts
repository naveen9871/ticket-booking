import { useState, useEffect, useCallback } from 'react'
import api from '../api'

export interface AuthUser {
  id: number
  email: string | null
  phone: string | null
  full_name: string | null
  is_admin: boolean
}

export function useAuth() {
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
    // Fetch user profile
    const meRes = await api.get('/auth/me', {
      headers: { Authorization: `Bearer ${tok}` },
    })
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

  return { token, user, login, logout, isLoggedIn: !!token }
}
