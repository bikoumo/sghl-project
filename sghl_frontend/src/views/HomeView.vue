<template>
  <div class="home">
    <div class="home__media" aria-hidden="true">
      <div class="home__wash"></div>
      <div class="home__pattern"></div>
    </div>

    <header class="home__top">
      <SghlLogo size="lg" light tagline="Système hospitalier localisé" />
      <button type="button" class="home__login-link" @click="goLogin">Connexion</button>
    </header>

    <section class="home__hero">
      <p class="home__brand">SGHL</p>
      <h1>Le portail qui relie soins, services et patients.</h1>
      <p class="home__sub">
        Gestion hospitalière localisée — sécurisée, claire, pensée pour le terrain.
      </p>
      <div class="home__actions">
        <button type="button" class="sghl-btn sghl-btn-primary" @click="goLogin">
          Accéder au portail
        </button>
        <button type="button" class="sghl-btn home__btn-secondary" @click="showAbout = true">
          Découvrir SGHL
        </button>
      </div>
    </section>

    <div v-if="showAbout" class="about-overlay" @click.self="showAbout = false">
      <div class="about-dialog sghl-panel" role="dialog" aria-modal="true" aria-labelledby="about-title">
        <div class="about-dialog__head">
          <h2 id="about-title">Découvrir SGHL</h2>
          <button type="button" class="about-close" aria-label="Fermer" @click="showAbout = false">✕</button>
        </div>
        <div class="about-dialog__body">
          <p><strong>Parcours complets</strong> — admissions, consultations, labo, pharmacie, hospitalisation et facturation.</p>
          <p><strong>Sécurité MFA</strong> — connexion email + code OTP, avec secours local si l’email est indisponible.</p>
          <p><strong>Droits par rôle</strong> — DG, secrétaires, médecins, biologistes et patients voient uniquement ce qui les concerne.</p>
        </div>
        <div class="about-dialog__foot">
          <button type="button" class="sghl-btn sghl-btn-primary" @click="showAbout = false">Fermer</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import SghlLogo from '@/components/SghlLogo.vue'

const router = useRouter()
const showAbout = ref(false)

const goLogin = () => {
  // Force l’écran de connexion même si une ancienne session est en cache
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  router.push({ name: 'login', query: { force: '1' } })
}
</script>

<style scoped>
.home {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  color: #f5fbf9;
  display: flex;
  flex-direction: column;
}

.home__media {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(120deg, rgba(3, 42, 52, 0.72), rgba(5, 72, 97, 0.55)),
    radial-gradient(ellipse at 70% 40%, #0f7a6b 0%, transparent 55%),
    linear-gradient(160deg, #032a34, #054861 55%, #0a5f6e);
}

.home__wash {
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, rgba(3, 42, 52, 0.55) 0%, rgba(3, 42, 52, 0.25) 45%, transparent 70%);
}

.home__pattern {
  position: absolute;
  inset: 0;
  opacity: 0.35;
  background-image:
    radial-gradient(circle at 20% 30%, rgba(212, 160, 23, 0.2) 0 1px, transparent 2px),
    radial-gradient(circle at 80% 70%, rgba(232, 244, 241, 0.15) 0 1px, transparent 2px);
  background-size: 56px 56px, 40px 40px;
  animation: sghl-drift 18s ease-in-out infinite;
}

.home__top,
.home__hero {
  position: relative;
  z-index: 1;
}

.home__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.4rem clamp(1.2rem, 4vw, 3rem);
  animation: sghl-fade-up 0.45s ease both;
}

.home__login-link {
  text-decoration: none;
  font-weight: 650;
  color: #f5fbf9;
  border: 1px solid rgba(245, 251, 249, 0.35);
  padding: 0.55rem 1rem;
  border-radius: var(--radius-sm);
  background: transparent;
  cursor: pointer;
  transition: background 0.2s ease, border-color 0.2s ease;
}

.home__login-link:hover {
  background: rgba(245, 251, 249, 0.1);
  border-color: rgba(245, 251, 249, 0.6);
}

.home__hero {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  padding: clamp(2rem, 8vh, 5rem) clamp(1.2rem, 4vw, 3rem) clamp(2.5rem, 8vh, 4.5rem);
  max-width: 760px;
  animation: sghl-fade-up 0.55s ease 0.08s both;
}

.home__brand {
  font-family: var(--font-display);
  font-size: clamp(3.2rem, 12vw, 6.5rem);
  font-weight: 700;
  letter-spacing: 0.06em;
  line-height: 0.95;
  margin-bottom: 0.8rem;
  background: linear-gradient(105deg, #fff 20%, #e8f4f1 55%, #d4a017 110%);
  background-size: 180% 100%;
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  animation: sghl-shimmer 8s ease-in-out infinite alternate;
}

.home__hero h1 {
  color: #fff;
  font-size: clamp(1.45rem, 3.2vw, 2.1rem);
  font-weight: 600;
  max-width: 18ch;
  margin-bottom: 0.75rem;
}

.home__sub {
  color: rgba(232, 244, 241, 0.85);
  font-size: 1.05rem;
  max-width: 36ch;
  margin-bottom: 1.6rem;
}

.home__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.home__btn-secondary {
  background: rgba(245, 251, 249, 0.12);
  color: #fff;
  border: 1px solid rgba(245, 251, 249, 0.28);
}

.home__btn-secondary:hover {
  background: rgba(245, 251, 249, 0.2);
}

.about-overlay {
  position: fixed;
  inset: 0;
  z-index: 40;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  background: rgba(3, 42, 52, 0.55);
  animation: sghl-fade-up 0.25s ease both;
}

.about-dialog {
  width: min(560px, 100%);
  padding: 1.4rem 1.5rem;
}

.about-dialog__head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.about-dialog__body {
  display: grid;
  gap: 0.75rem;
  color: var(--sghl-muted);
  font-size: 0.95rem;
}

.about-dialog__body strong {
  color: var(--sghl-ink);
  font-weight: 700;
}

.about-dialog__foot {
  margin-top: 1.4rem;
  text-align: right;
}

.about-close {
  border: none;
  background: transparent;
  font-size: 1.1rem;
  cursor: pointer;
  color: var(--sghl-muted);
}
</style>
