/**
 * Base URL API — fonctionne en local, Wi‑Fi, ET en production (Netlify / Render).
 *
 * Ordre de résolution :
 * 1. VITE_API_URL       — URL racine du backend (ex: https://sghl-backend.onrender.com)
 *                        → /api/v2 est ajouté automatiquement
 *                        → À définir dans les variables d'env Netlify (ou .env.local)
 * 2. VITE_API_BASE_URL  — URL complète avec le préfixe /api/v2
 *                        (utilisé par build-render.sh sur Render)
 * 3. PRODUCTION         — import.meta.env.PROD === true (Netlify / build)
 *                        → https://sghl-backend.onrender.com/api/v2
 * 4. Détection auto     — http://{hostname}:8000/api/v2 (local / Wi‑Fi)
 * 5. Fallback           — http://127.0.0.1:8000/api/v2
 */
export function getApiBaseUrl() {
  // 1. Variable d'env VITE_API_URL (priorité max — configurable dans Netlify dashboard)
  if (import.meta.env.VITE_API_URL) {
    const base = import.meta.env.VITE_API_URL.replace(/\/$/, '')
    return `${base}/api/v2`
  }

  // 2. Variable d'env VITE_API_BASE_URL (utilisée par build-render.sh sur Render)
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL.replace(/\/$/, '')
  }

  // 3. Production (Netlify, Render static site, etc.) — backend Render par défaut
  if (import.meta.env.PROD) {
    return 'https://sghl-backend.onrender.com/api/v2'
  }

  // 4. Développement local / Wi‑Fi — détection automatique du hostname
  if (typeof window !== 'undefined' && window.location?.hostname) {
    const host = window.location.hostname
    return `http://${host}:8000/api/v2`
  }

  // 5. Fallback final
  return 'http://127.0.0.1:8000/api/v2'
}

export const apiBaseUrl = getApiBaseUrl()
