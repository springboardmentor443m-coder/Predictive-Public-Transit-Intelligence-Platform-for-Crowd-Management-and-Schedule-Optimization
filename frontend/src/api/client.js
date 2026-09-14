import axios from 'axios'

const api = axios.create({ baseURL: '' })
api.interceptors.request.use((c) => {
  const t = localStorage.getItem('token')
  if (t) c.headers.Authorization = `Bearer ${t}`
  return c
})
export default api
export const login = (u, p) => {
  const f = new URLSearchParams({ username: u, password: p })
  return api.post('/api/auth/login', f)
}

// Role helpers: role is stored at login (from /api/auth/me)
export const getRole = () => localStorage.getItem('role') || 'viewer'
export const getUsername = () => localStorage.getItem('username') || ''
export const isViewer = () => getRole() === 'viewer'
export const canOperate = () => ['operator', 'admin'].includes(getRole())
export const isAdmin = () => getRole() === 'admin'
export const logout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('role')
  localStorage.removeItem('username')
}
