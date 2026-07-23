/**
 * Base URL API — fonctionne en local ET depuis le téléphone (même Wi‑Fi).
 * Ex: page sur http://192.168.x.x:5174 → API sur http://192.168.x.x:8000/api/v2
 */
export function getApiBaseUrl() {
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL.replace(/\/$/, '')
  }
  if (typeof window !== 'undefined' && window.location?.hostname) {
    const host = window.location.hostname
    return `http://${host}:8000/api/v2`
  }
  return 'http://127.0.0.1:8000/api/v2'
}

export const apiBaseUrl = getApiBaseUrl()
