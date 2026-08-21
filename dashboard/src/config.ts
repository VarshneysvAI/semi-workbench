const ENV_API = import.meta.env.VITE_API_URL || ''
const DEFAULT_API = import.meta.env.DEV ? 'http://localhost:8000' : ''
export const API_BASE = (ENV_API || DEFAULT_API).replace(/\/$/, '')

export const getApiUrl = (path: string) => {
  const cleanPath = path.startsWith('/') ? path : `/${path}`
  return `${API_BASE}${cleanPath}`
}
