import axios from 'axios'

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v2'

const api = axios.create({
  baseURL: apiBaseUrl,
  headers: {
    'Content-Type': 'application/json',
  }
})

api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export default {
  instance: api,

  // Authentification : Appel direct sur /api/v1/auth/...
  login(credentials) {
    return api.post('/auth/login/', credentials)
  },

  verifyMfa(data) {
    return api.post('/auth/verify-mfa/', data)
  },

  // Module Clinique : Préfixé par /clinical/ comme attendu
  getPatients() {
    return api.get('/clinical/patients/')
  },

  // Gestion des factures
  getInvoices() {
    return api.get('/finance/invoices/') 
  },

  addPayment(invoiceId, data) {
    return api.post(`/finance/invoices/${invoiceId}/add-payment/`, data)
  }
}