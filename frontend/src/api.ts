import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8001/api/v1'

export const api = axios.create({ baseURL: BASE_URL, timeout: 15000 })

// Auto-attach JWT token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('ticketly_token')
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Redirect on 401
api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('ticketly_token')
      localStorage.removeItem('ticketly_user')
      window.dispatchEvent(new Event('ticketly:logout'))
    }
    return Promise.reject(error)
  },
)

export default api
