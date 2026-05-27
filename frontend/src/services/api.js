import axios from 'axios'
import { useStore } from '../stores/useStore.js'

const createApi = () => {
  const apiBaseUrl = useStore.getState().apiBaseUrl || 'http://localhost:8000'

  const api = axios.create({
    baseURL: apiBaseUrl,
    headers: {
      'Content-Type': 'application/json',
    },
  })

  // Request interceptor - attach JWT token
  api.interceptors.request.use(
    (config) => {
      const token = useStore.getState().token
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
      return config
    },
    (error) => Promise.reject(error)
  )

  // Response interceptor - handle 401 and errors
  api.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response?.status === 401) {
        useStore.getState().logout()
        window.location.href = '/login'
      }
      return Promise.reject(error)
    }
  )

  return api
}

let apiInstance = null

export const getApi = () => {
  if (!apiInstance) {
    apiInstance = createApi()
  }
  return apiInstance
}

// Health check
export const healthCheck = async () => {
  const api = getApi()
  const response = await api.get('/health')
  return response.data
}

// Auth
export const login = async (credentials) => {
  const api = getApi()
  const response = await api.post('/api/v1/auth/login', credentials)
  return response.data
}

export const register = async (data) => {
  const api = getApi()
  const response = await api.post('/api/v1/auth/register', data)
  return response.data
}

// Research
export const startResearch = async (data) => {
  const api = getApi()
  const response = await api.post('/api/v1/research', data)
  return response.data
}

export const getResearchStatus = async (sessionId) => {
  const api = getApi()
  const response = await api.get(`/api/v1/research/${sessionId}`)
  return response.data
}

export const getResearchReport = async (sessionId) => {
  const api = getApi()
  const response = await api.get(`/api/v1/research/${sessionId}/report`)
  return response.data
}

// Reports
export const listReports = async () => {
  const api = getApi()
  const response = await api.get('/api/v1/reports')
  return response.data
}

// Documents
export const listDocuments = async () => {
  const api = getApi()
  const response = await api.get('/api/v1/documents')
  return response.data
}

export const uploadDocument = async (file) => {
  const api = getApi()
  const formData = new FormData()
  formData.append('file', file)
  const response = await api.post('/api/v1/documents/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return response.data
}

// Graphs
export const listEntities = async () => {
  const api = getApi()
  const response = await api.get('/api/v1/graphs/entities')
  return response.data
}
