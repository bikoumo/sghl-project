<template>
  <div class="login-page">
    <aside class="login-brand" aria-label="Présentation SGHL">
      <div class="login-brand__aurora" aria-hidden="true"></div>
      <div class="login-brand__grid" aria-hidden="true"></div>
      <div class="login-brand__orb" aria-hidden="true"></div>
      <div class="login-brand__content">
        <SghlLogo size="xl" light tagline="Portail hospitalier sécurisé" />
        <p class="login-brand__kicker">Système de Gestion Hospitalière Localisée</p>
        <h1 class="login-brand__title">Soigner mieux,<br>décider plus vite.</h1>
        <p class="login-brand__lead">
          Un portail unique pour le personnel et les patients — consultations,
          admissions, pharmacie et paiements, protégés par MFA.
        </p>
        <ul class="login-brand__points">
          <li>Accès filtrés par rôle et par service</li>
          <li>Connexion sécurisée en deux étapes</li>
          <li>Suivi clinique et logistique en direct</li>
        </ul>
      </div>
      <p class="login-brand__footer">SGHL · Confiance · Continuité des soins</p>
    </aside>

    <main class="login-panel">
      <div class="login-panel__card">
        <header class="login-panel__header">
          <div class="login-panel__mobile-logo">
            <SghlLogo size="md" tagline="Connexion sécurisée" />
          </div>
          <h2>{{ showVerification ? 'Vérification MFA' : 'Connexion' }}</h2>
          <p v-if="!showVerification">Identifiez-vous pour accéder à votre espace.</p>
          <p v-else-if="emailSent">Saisissez le code reçu par email.</p>
          <p v-else>Email indisponible — utilisez le code de secours ci-dessous.</p>
        </header>

        <div v-if="errorMessage" class="banner banner--error" role="alert">{{ errorMessage }}</div>
        <div v-if="infoMessage" class="banner banner--info" role="status">{{ infoMessage }}</div>

        <form class="login-form" @submit.prevent="handleLogin">
          <div v-if="showVerification" class="mfa-step">
            <div v-if="fallbackCode" class="fallback-panel" role="status">
              <span class="fallback-label">Code généré</span>
              <div class="fallback-code-row">
                <code class="fallback-code" aria-live="polite">{{ fallbackCode }}</code>
                <button type="button" class="btn-copy" @click="copyFallbackCode">
                  {{ copied ? 'Copié' : 'Copier' }}
                </button>
              </div>
              <p class="fallback-hint">
                L’envoi par email a échoué. Copiez ce code à 6 chiffres ou saisissez-le manuellement.
              </p>
            </div>

            <div class="sghl-field">
              <label for="code">Code de sécurité</label>
              <input
                id="code"
                v-model="verificationCode"
                type="text"
                inputmode="numeric"
                pattern="[0-9]{6}"
                maxlength="6"
                autocomplete="one-time-code"
                placeholder="000000"
                required
              />
            </div>
            <p v-if="mfaSecondsLeft > 0" class="mfa-timer">Code valide encore {{ mfaTimerLabel }}</p>
            <p v-else class="mfa-timer mfa-timer--expired">Code expiré — renvoyez un nouveau code.</p>
            <button type="button" class="sghl-btn-ghost mfa-resend" :disabled="loading" @click="resendMfaCode">
              Renvoyer le code
            </button>
          </div>

          <template v-else>
            <div class="sghl-field">
              <label for="email">Adresse email</label>
              <input
                id="email"
                v-model="email"
                type="email"
                placeholder="nom@hopital.com"
                autocomplete="username"
                required
              />
            </div>
            <div class="sghl-field">
              <label for="password">Mot de passe</label>
              <input
                id="password"
                v-model="password"
                type="password"
                placeholder="••••••••"
                autocomplete="current-password"
                required
              />
            </div>
            <div class="sghl-field">
              <label for="role">Rôle</label>
              <select id="role" v-model="selectedRole">
                <option value="PATIENT">Patient</option>
                <option value="DOCTOR">Médecin</option>
                <option value="DG">Directeur Général</option>
                <option value="SECRETARY_GENERAL">Secrétaire Générale</option>
                <option value="SECRETARY_SERVICE">Secrétaire de Service</option>
                <option value="BIOLOGIST">Biologiste / Pharmacie</option>
              </select>
            </div>
            <div
              v-if="selectedRole === 'DOCTOR' || selectedRole === 'SECRETARY_SERVICE'"
              class="sghl-field"
            >
              <label for="service">Service (vérification)</label>
              <input
                id="service"
                v-model="selectedService"
                type="text"
                placeholder="Ex: PED"
              />
            </div>
          </template>

          <button type="submit" class="sghl-btn sghl-btn-primary login-submit" :disabled="loading">
            {{ loading ? 'En cours…' : (showVerification ? 'Valider le code' : 'Se connecter') }}
          </button>

          <button
            v-if="showVerification"
            type="button"
            class="sghl-btn sghl-btn-ghost"
            :disabled="loading"
            @click="resetMfaStep"
          >
            Retour
          </button>
        </form>

        <p class="login-panel__hint">
          Votre rôle en base prime sur le sélecteur — celui-ci sert uniquement de vérification.
        </p>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import api from '@/api';
import SghlLogo from '@/components/SghlLogo.vue';

const email = ref('');
const password = ref('');
const verificationCode = ref('');
const selectedRole = ref('PATIENT');
const selectedService = ref('');
const showVerification = ref(false);
const emailSent = ref(false);
const fallbackCode = ref(null);
const copied = ref(false);
const errorMessage = ref('');
const infoMessage = ref('');
const loading = ref(false);
const router = useRouter();
const route = useRoute();
const storedUsername = ref('');
const mfaSecondsLeft = ref(0);
let mfaTimerId = null;

const mfaTimerLabel = computed(() => {
  const m = Math.floor(mfaSecondsLeft.value / 60);
  const s = mfaSecondsLeft.value % 60;
  return `${m}:${String(s).padStart(2, '0')}`;
});

const startMfaTimer = () => {
  mfaSecondsLeft.value = 300;
  if (mfaTimerId) clearInterval(mfaTimerId);
  mfaTimerId = setInterval(() => {
    if (mfaSecondsLeft.value > 0) mfaSecondsLeft.value -= 1;
    else if (mfaTimerId) clearInterval(mfaTimerId);
  }, 1000);
};

const stopMfaTimer = () => {
  if (mfaTimerId) clearInterval(mfaTimerId);
  mfaTimerId = null;
  mfaSecondsLeft.value = 0;
};

onUnmounted(stopMfaTimer);

const getDashboardRoute = (role) => {
  const normalizedRole = (role || '').toUpperCase();
  if (normalizedRole === 'DOCTOR' || normalizedRole === 'BIOLOGIST') return '/dashboard/doctor';
  if (normalizedRole === 'PATIENT') return '/dashboard/patient';
  if (normalizedRole === 'ADMIN' || normalizedRole === 'DG') return '/dashboard/admin';
  if (
    normalizedRole === 'SECRETARY' ||
    normalizedRole === 'SECRETARY_GENERAL' ||
    normalizedRole === 'SECRETARY_SERVICE'
  ) {
    return '/dashboard/secretary';
  }
  return '/dashboard';
};

const persistSession = async (data) => {
  const userPayload = {
    ...data,
    role: data.role,
    service: data.service || null,
  };
  if (data.token) localStorage.setItem('token', data.token);
  localStorage.setItem('user', JSON.stringify(userPayload));

  const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '';
  const safeRedirect = redirect.startsWith('/') && !redirect.startsWith('//') ? redirect : '';
  const target = safeRedirect || getDashboardRoute(userPayload.role);
  try {
    await router.replace(target);
  } catch (navError) {
    console.error('Navigation après login échouée:', navError);
    window.location.assign(target);
  }
};

const resetMfaStep = () => {
  showVerification.value = false;
  verificationCode.value = '';
  fallbackCode.value = null;
  emailSent.value = false;
  infoMessage.value = '';
  errorMessage.value = '';
  copied.value = false;
  stopMfaTimer();
};

const resendMfaCode = async () => {
  if (loading.value || !storedUsername.value) return;
  loading.value = true;
  errorMessage.value = '';
  try {
    const response = await api.resendMfa({ username: storedUsername.value });
    const data = response.data || response;
    emailSent.value = Boolean(data.email_sent);
    fallbackCode.value = data.fallback_code || null;
    if (fallbackCode.value) {
      verificationCode.value = fallbackCode.value;
      infoMessage.value = 'Nouveau code de secours généré.';
    } else {
      infoMessage.value = 'Un nouveau code a été envoyé par email.';
    }
    startMfaTimer();
  } catch (error) {
    errorMessage.value = error?.response?.data?.detail || 'Impossible de renvoyer le code.';
  } finally {
    loading.value = false;
  }
};

const copyFallbackCode = async () => {
  if (!fallbackCode.value) return;
  try {
    await navigator.clipboard.writeText(fallbackCode.value);
    verificationCode.value = fallbackCode.value;
    copied.value = true;
    setTimeout(() => { copied.value = false; }, 2000);
  } catch {
    verificationCode.value = fallbackCode.value;
  }
};

const handleLogin = async () => {
  if (loading.value) return;
  loading.value = true;
  errorMessage.value = '';
  infoMessage.value = '';

  try {
    if (!showVerification.value) {
      const response = await api.login({
        username: email.value,
        password: password.value,
        role: selectedRole.value,
        service: selectedService.value,
      });
      const data = response.data || response;

      if (data.requires_mfa) {
        storedUsername.value = data.username || email.value;
        emailSent.value = Boolean(data.email_sent);
        fallbackCode.value = data.fallback_code || null;
        if (fallbackCode.value) {
          verificationCode.value = fallbackCode.value;
          infoMessage.value = 'Code de secours disponible — validez pour continuer.';
        } else {
          infoMessage.value = 'Un code a été envoyé à votre adresse email.';
        }
        showVerification.value = true;
        startMfaTimer();
        loading.value = false;
        return;
      }

      if (data.status === 'success' && data.token) {
        await persistSession(data);
        return;
      }

      errorMessage.value = data.message || 'Connexion impossible.';
    } else {
      const response = await api.verifyMfa({
        username: storedUsername.value,
        code: String(verificationCode.value || '').trim(),
      });
      const data = response.data || response;

      if (data.status === 'success' && data.token) {
        await persistSession(data);
        return;
      }

      errorMessage.value = data.message || 'Code incorrect.';
    }
  } catch (error) {
    const detail = error?.response?.data?.detail;
    const detailText = typeof detail === 'string'
      ? detail
      : Array.isArray(detail)
        ? detail.map((d) => d.msg || d).join(' ')
        : null;
    errorMessage.value =
      detailText ||
      error?.response?.data?.message ||
      (error?.code === 'ERR_NETWORK'
        ? 'Serveur inaccessible. Vérifiez que l’API tourne sur le port 8000.'
        : 'Erreur de connexion.');
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(340px, 0.85fr);
  background: #e8eef7;
}

.login-brand {
  position: relative;
  overflow: hidden;
  color: #f8fafc;
  padding: clamp(2rem, 5vw, 4.25rem);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  background:
    radial-gradient(ellipse 70% 50% at 15% 15%, rgba(96, 165, 250, 0.28), transparent 55%),
    radial-gradient(ellipse 55% 45% at 90% 85%, rgba(37, 99, 235, 0.35), transparent 50%),
    linear-gradient(155deg, #071535 0%, #0b1f4a 42%, #1e3a8a 100%);
}

.login-brand__aurora {
  position: absolute;
  inset: -18% auto auto -8%;
  width: 65%;
  height: 50%;
  background: linear-gradient(120deg, rgba(147, 197, 253, 0.2), rgba(59, 130, 246, 0.08), transparent);
  filter: blur(32px);
  animation: sghl-drift 14s ease-in-out infinite;
  pointer-events: none;
}

.login-brand__orb {
  position: absolute;
  right: -8%;
  bottom: 8%;
  width: min(340px, 48vw);
  height: min(340px, 48vw);
  border-radius: 50%;
  border: 1px solid rgba(147, 197, 253, 0.22);
  background: radial-gradient(circle at 35% 35%, rgba(96, 165, 250, 0.18), transparent 65%);
  animation: sghl-drift 18s ease-in-out infinite reverse;
  pointer-events: none;
}

.login-brand__grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(147, 197, 253, 0.07) 1px, transparent 1px),
    linear-gradient(90deg, rgba(147, 197, 253, 0.07) 1px, transparent 1px);
  background-size: 44px 44px;
  mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0.5), transparent 88%);
  pointer-events: none;
}

.login-brand__content {
  position: relative;
  z-index: 1;
  max-width: 36rem;
  animation: sghl-fade-up 0.6s ease both;
}

.login-brand__kicker {
  margin-top: 1.75rem;
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #93c5fd;
}

.login-brand__title {
  margin-top: 0.9rem;
  font-family: var(--font-display, 'Sora', sans-serif);
  font-size: clamp(2.15rem, 4.2vw, 3.2rem);
  font-weight: 800;
  line-height: 1.1;
  color: #fff;
  letter-spacing: -0.025em;
}

.login-brand__lead {
  margin-top: 1.15rem;
  font-size: 1.05rem;
  line-height: 1.7;
  color: rgba(226, 232, 240, 0.88);
  max-width: 34ch;
}

.login-brand__points {
  margin-top: 1.9rem;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 0.85rem;
}

.login-brand__points li {
  position: relative;
  padding-left: 1.4rem;
  color: rgba(248, 250, 252, 0.92);
  font-size: 0.95rem;
  font-weight: 500;
}

.login-brand__points li::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0.5em;
  width: 0.5rem;
  height: 0.5rem;
  border-radius: 2px;
  background: #60a5fa;
}

.login-brand__footer {
  position: relative;
  z-index: 1;
  margin-top: 3rem;
  font-size: 0.8rem;
  letter-spacing: 0.06em;
  color: rgba(191, 219, 254, 0.65);
}

.login-panel {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: clamp(1.5rem, 4vw, 3rem);
  background:
    radial-gradient(circle at 100% 0%, rgba(37, 99, 235, 0.1), transparent 40%),
    linear-gradient(180deg, #eef3fb 0%, #e2e9f5 100%);
}

.login-panel__card {
  width: 100%;
  max-width: 440px;
  padding: clamp(1.5rem, 3vw, 2.1rem);
  border-radius: 18px;
  background: #fff;
  border: 1px solid rgba(11, 31, 74, 0.1);
  box-shadow: 0 18px 40px rgba(11, 31, 74, 0.12);
  animation: sghl-fade-up 0.55s ease 0.08s both;
}

.login-panel__mobile-logo {
  display: none;
  margin-bottom: 1.25rem;
}

.login-panel__header h2 {
  font-size: 1.75rem;
  margin-bottom: 0.4rem;
  color: #0b1f4a;
  font-weight: 800;
  letter-spacing: -0.02em;
}

.login-panel__header p {
  color: #64748b;
  font-size: 0.95rem;
  margin-bottom: 1.35rem;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 1.05rem;
}

.login-form :deep(.sghl-field label) {
  color: #0b1f4a;
  font-weight: 700;
}

.login-form :deep(.sghl-field input),
.login-form :deep(.sghl-field select) {
  border-color: rgba(11, 31, 74, 0.16);
  background: #f8fafc;
}

.login-form :deep(.sghl-field input:focus),
.login-form :deep(.sghl-field select:focus) {
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.16);
  background: #fff;
}

.mfa-step {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.banner {
  padding: 0.8rem 0.95rem;
  border-radius: 10px;
  font-size: 0.9rem;
  margin-bottom: 1rem;
  text-align: left;
}

.banner--error {
  background: #fef2f2;
  color: #b91c1c;
  border: 1px solid rgba(185, 28, 28, 0.18);
}

.banner--info {
  background: #eff6ff;
  color: #1e3a8a;
  border: 1px solid rgba(30, 58, 138, 0.16);
}

.fallback-panel {
  background: #eff6ff;
  border: 1px dashed rgba(37, 99, 235, 0.35);
  border-radius: 12px;
  padding: 1rem 1.1rem;
  text-align: center;
}

.fallback-label {
  display: block;
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #1e3a8a;
  margin-bottom: 0.65rem;
}

.fallback-code-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.65rem;
  flex-wrap: wrap;
}

.fallback-code {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 1.55rem;
  font-weight: 700;
  letter-spacing: 0.28em;
  color: #0b1f4a;
  background: #fff;
  padding: 0.55rem 0.9rem;
  border-radius: 10px;
  border: 1px solid rgba(11, 31, 74, 0.14);
}

.btn-copy {
  border: 1px solid #1e3a8a;
  background: #0b1f4a;
  color: #fff;
  padding: 0.55rem 0.9rem;
  border-radius: 10px;
  font-size: 0.85rem;
  font-weight: 650;
  cursor: pointer;
}

.btn-copy:hover {
  background: #1e3a8a;
}

.fallback-hint {
  margin: 0.75rem 0 0;
  font-size: 0.8rem;
  color: #64748b;
  line-height: 1.45;
}

.mfa-timer {
  font-size: 0.82rem;
  font-weight: 600;
  color: #1e3a8a;
  text-align: center;
}

.mfa-timer--expired {
  color: #b91c1c;
}

.mfa-resend {
  align-self: center;
  font-size: 0.88rem;
}

.login-submit {
  width: 100%;
  margin-top: 0.35rem;
  background: linear-gradient(135deg, #0b1f4a, #1e3a8a 55%, #2563eb) !important;
  color: #fff !important;
  border: none;
  box-shadow: 0 10px 24px rgba(11, 31, 74, 0.28);
}

.login-submit:hover:not(:disabled) {
  filter: brightness(1.06);
}

.login-form :deep(.sghl-btn-ghost) {
  color: #1e3a8a;
  font-weight: 650;
}

.login-panel__hint {
  margin-top: 1.35rem;
  font-size: 0.78rem;
  color: #64748b;
  line-height: 1.5;
}

@media (max-width: 900px) {
  .login-page {
    grid-template-columns: 1fr;
  }

  .login-brand {
    min-height: 40vh;
    padding-bottom: 2rem;
  }

  .login-brand__title {
    margin-top: 0.75rem;
    font-size: clamp(1.7rem, 7vw, 2.25rem);
  }

  .login-brand__points,
  .login-brand__footer,
  .login-brand__orb {
    display: none;
  }

  .login-panel__mobile-logo {
    display: block;
  }
}
</style>
