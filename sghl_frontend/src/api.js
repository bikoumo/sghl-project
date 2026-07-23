import axios from 'axios'
import { getApiBaseUrl } from './apiBase'

const apiBaseUrl = getApiBaseUrl()

const api = axios.create({
  baseURL: apiBaseUrl,
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
        window.location.assign('/login?force=1')
      }
    }
    return Promise.reject(error)
  },
)

export async function downloadAuthenticatedFile(url, filename) {
  const response = await api.get(url, { responseType: 'blob' })
  const blob = new Blob([response.data])
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = filename
  link.click()
  URL.revokeObjectURL(link.href)
}

export default {
  instance: api,

  login(credentials) {
    return api.post('/auth/login/', credentials)
  },

  verifyMfa(data) {
    return api.post('/auth/verify-mfa/', data)
  },

  resendMfa(data) {
    return api.post('/auth/resend-mfa/', data)
  },

  getPatients() {
    return api.get('/clinical/patients/')
  },

  getInvoices() {
    return api.get('/clinical/invoices/')
  },

  addPayment(invoiceId, data) {
    return api.post(`/clinical/invoices/${invoiceId}/pay`, data)
  },

  exportInvoicesCsv() {
    return downloadAuthenticatedFile('/clinical/invoices/export', 'factures_sghl.csv')
  },

  exportStaffCsv() {
    return downloadAuthenticatedFile('/finance/staff/export', 'personnel_sghl.csv')
  },

  searchPatients(query) {
    return api.get(`/clinical/patients/search`, { params: { q: query } })
  },

  createInvoice(data) {
    return api.post('/clinical/invoices/create', data)
  },
}
