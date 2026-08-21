export const API_BASE = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '')
export const getApiUrl = (path: string) => {
  const cleanPath = path.startsWith('/') ? path : `/${path}`
  return `${API_BASE}${cleanPath}`
}
