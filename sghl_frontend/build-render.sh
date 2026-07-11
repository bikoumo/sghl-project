#!/usr/bin/env bash
set -euo pipefail

if [ -n "${BACKEND_URL:-}" ]; then
  export VITE_API_BASE_URL="${BACKEND_URL%/}/api/v2"
  echo "VITE_API_BASE_URL=${VITE_API_BASE_URL}"
else
  echo "BACKEND_URL non défini — fallback sur la valeur par défaut de api.js"
fi

npm ci
npm run build
