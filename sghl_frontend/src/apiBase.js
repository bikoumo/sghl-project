/**
 * Base URL API — fonctionne en local ET depuis le téléphone (même Wi‑Fi).
 * Ex: page sur http://192.168.x.x:5174 → API sur http://192.168.x.x:8000/api/v2
 *
 * Ordre de résolution :
 * 1. VITE_API_URL       — URL racine du backend (ex: https://sghl-backend.onrender.com)
 *                        → /api/v2 est ajouté automatiquement
 * 2. VITE_API_BASE_URL  — URL complète avec le préfixe /api/v2
 *                        (utilisé par build-render.sh sur Render)
 * 3. Détection auto     — http://{hostname}:8000/api/v2 (local / Wi‑Fi)
 * 4. Fallback           — http://127.0.0.1:8000/api/v2
 */
export function getApiBaseUrl() {
  if (import.meta.env.VITE_API_URL) {
    const base = import.meta.env.VITE_API_URL.replace(/\/$/, '')
    return `${base}/api/v2`
  }
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
