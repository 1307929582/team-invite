import axios from 'axios'
import { message } from 'antd'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/admin/login'
    }
    message.error(error.response?.data?.detail || '请求失败')
    return Promise.reject(error)
  }
)

// Auth API
export const authApi = {
  login: (username: string, password: string) => {
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)
    return api.post('/auth/login', formData)
  },
  getMe: () => api.get('/auth/me'),
  initAdmin: () => api.post('/auth/init-admin'),
}

// Team API
export const teamApi = {
  list: () => api.get('/teams'),
  get: (id: number) => api.get(`/teams/${id}`),
  create: (data: any) => api.post('/teams', data),
  update: (id: number, data: any) => api.put(`/teams/${id}`, data),
  delete: (id: number) => api.delete(`/teams/${id}`),
  getMembers: (id: number) => api.get(`/teams/${id}/members`),
  syncMembers: (id: number) => api.post(`/teams/${id}/sync`),
  verifyToken: (id: number) => api.post(`/teams/${id}/verify-token`),
  getSubscription: (id: number) => api.get(`/teams/${id}/subscription`),
  getPendingInvites: (id: number) => api.get(`/teams/${id}/pending-invites`),
}

// Invite API
export const inviteApi = {
  batchInvite: (teamId: number, emails: string[]) => 
    api.post(`/teams/${teamId}/invites`, { emails }),
  getRecords: (teamId: number) => api.get(`/teams/${teamId}/invites`),
  getPending: (teamId: number) => api.get(`/teams/${teamId}/invites/pending`),
}

// Dashboard API
export const dashboardApi = {
  getStats: () => api.get('/dashboard/stats'),
  getLogs: (limit?: number, teamId?: number) => 
    api.get('/dashboard/logs', { params: { limit, team_id: teamId } }),
  getSeats: () => api.get('/dashboard/seats'),
}

// Redeem Code API
export const redeemApi = {
  list: (teamId?: number, isActive?: boolean) => 
    api.get('/redeem-codes', { params: { team_id: teamId, is_active: isActive } }),
  batchCreate: (data: { max_uses: number; expires_days?: number; count: number; prefix?: string }) =>
    api.post('/redeem-codes/batch', data),
  delete: (id: number) => api.delete(`/redeem-codes/${id}`),
  toggle: (id: number) => api.put(`/redeem-codes/${id}/toggle`),
}

// Config API
export const configApi = {
  list: () => api.get('/config'),
  update: (key: string, value: string) => api.put(`/config/${key}`, { key, value }),
  batchUpdate: (configs: { key: string; value: string; description?: string | null }[]) => 
    api.post('/config/batch', configs),
}

// LinuxDO User API
export const linuxdoUserApi = {
  list: (search?: string, hasInvite?: boolean) => 
    api.get('/linuxdo-users', { params: { search, has_invite: hasInvite } }),
  get: (id: number) => api.get(`/linuxdo-users/${id}`),
}

// Setup API (无需认证)
export const setupApi = {
  getStatus: () => axios.get('/api/v1/setup/status').then(r => r.data),
  initialize: (data: { username: string; email: string; password: string; confirm_password: string }) =>
    axios.post('/api/v1/setup/initialize', data).then(r => r.data),
}

// Public API (无需认证)
const publicApiClient = axios.create({
  baseURL: '/api/v1/public',
  timeout: 30000,
})

publicApiClient.interceptors.response.use(
  (response) => response.data,
  (error) => Promise.reject(error)
)

export const publicApi = {
  getLinuxDOAuthUrl: () => publicApiClient.get('/linuxdo/auth'),
  linuxdoCallback: (code: string, state: string) => publicApiClient.post('/linuxdo/callback', { code, state }),
  getUserStatus: (token: string) => publicApiClient.get('/user/status', { params: { token } }),
  redeem: (data: { email: string; redeem_code: string; linuxdo_token: string }) =>
    publicApiClient.post('/redeem', data),
  getSeats: () => publicApiClient.get('/seats'),
}

export default api
