import axios from 'axios'

// Create axios instance with base configuration
const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use((config) => {
  console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`)
  return config
})

// Response interceptor
api.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`)
    return response
  },
  (error) => {
    console.error(`API Error: ${error.response?.status} ${error.config?.url}`, error.response?.data)
    return Promise.reject(error)
  }
)

// Transactions API
export const transactionsApi = {
  getAll: (category = '') => {
    const params = category ? { category } : {}
    return api.get('/transactions', { params })
  },
  upload: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120000, // 2 minutes for CSV processing
    })
  },
  updateCategory: (transactionId, category, remember = true) =>
    api.put(`/transactions/${transactionId}/category`, { category, remember }),
}

// Categories API
export const categoriesApi = {
  getAll: () => api.get('/categories'),
}

// Analytics API
export const analyticsApi = {
  getSpendingTrends: (months = 12) => 
    api.get('/analytics/spending-trends', { params: { months } }),
  getCategorySummary: () => 
    api.get('/analytics/category-summary'),
  getExpenseSummary: () =>
    api.get('/expenses/summary'),
}

// Receipts API
export const receiptsApi = {
  upload: (files) => {
    const formData = new FormData()
    Array.from(files).forEach((file) => {
      formData.append('files', file)
    })
    return api.post('/receipts/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 300000, // 5 minutes for OCR processing
    })
  },
  list: () => api.get('/receipts/list'),
  getFolder: (month) => api.get(`/receipts/folder/${month}`),
}

// Settings API
export const settingsApi = {
  // Communal Expense Types
  getCommunalExpenseTypes: () => api.get('/settings/communal-expenses/types'),
  createCommunalExpenseType: (data) => api.post('/settings/communal-expenses/types', data),
  updateCommunalExpenseType: (id, data) => api.put(`/settings/communal-expenses/types/${id}`, data),
  deleteCommunalExpenseType: (id) => api.delete(`/settings/communal-expenses/types/${id}`),

  // Communal Expenses
  getCommunalExpenses: () => api.get('/settings/communal-expenses'),
  createCommunalExpense: (data) => api.post('/settings/communal-expenses', data),
  updateCommunalExpense: (id, data) => api.put(`/settings/communal-expenses/${id}`, data),
  deleteCommunalExpense: (id) => api.delete(`/settings/communal-expenses/${id}`),

  // Reset endpoints
  resetCommunalExpenses: () => api.delete('/settings/reset/communal-expenses'),

  // User Settings
  getUserSettings: () => api.get('/settings/user'),
  updateUserSettings: (data) => api.put('/settings/user', data),
}

// Reset API
export const resetApi = {
  transactions: () => api.delete('/reset/transactions'),
  categories: () => api.delete('/reset/categories'),
  all: () => api.delete('/reset/all'),
  refunds: () => api.post('/remove-refunds'),
}

export default api