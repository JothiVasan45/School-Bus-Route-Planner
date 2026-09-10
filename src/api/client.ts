import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
  timeout: 120000,
})

export default api

// API helpers
export const dataApi = {
  generate: (params: object) => api.post('/data/generate', params),
  preview: () => api.get('/data/preview'),
  stops: () => api.get('/data/stops'),
  buses: () => api.get('/data/buses'),
  drivers: () => api.get('/data/drivers'),
  stats: () => api.get('/data/stats'),
}

export const optimizationApi = {
  run: (params: object) => api.post('/optimization/run', params),
  list: (type?: string) => api.get('/optimization/list', { params: { optimization_type: type } }),
  getRoute: (id: string) => api.get(`/optimization/${id}`),
}

export const routeApi = {
  list: (type?: string) => api.get('/routes', { params: { optimization_type: type } }),
  get: (id: string) => api.get(`/routes/${id}`),
}

export const simulationApi = {
  run: (params: object) => api.post('/simulation/reliability', params),
}

export const dashboardApi = {
  get: () => api.get('/dashboard'),
}

export const workloadApi = {
  get: (type?: string) => api.get('/workload', { params: { optimization_type: type } }),
}

export const comparisonApi = {
  get: () => api.get('/comparison'),
}

export const overrideApi = {
  create: (params: object) => api.post('/override', params),
  log: () => api.get('/override/log'),
}

export const fallbackApi = {
  status: () => api.get('/fallback/status'),
  toggle: (params: object) => api.post('/fallback/toggle', params),
  manualUpdate: (params: object) => api.post('/fallback/manual-update', params),
  sync: () => api.post('/fallback/sync'),
  queue: () => api.get('/fallback/queue'),
  events: () => api.get('/fallback/events'),
}

export const experimentsApi = {
  run: (params: object) => api.post('/experiments/run', params),
  results: (id?: string) => api.get('/experiments/results', { params: { experiment_id: id } }),
}

export const validationApi = {
  submit: (params: object) => api.post('/validation', params),
  summary: () => api.get('/validation/summary'),
}

export const reportsApi = {
  evaluation: (format: string) => api.get('/reports/evaluation', { params: { format }, responseType: format === 'json' ? 'json' : 'blob' }),
}
