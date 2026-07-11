<template>
  <div class="home-shell">
    <section class="hero-card">
      <div>
        <p class="eyebrow">SGHL • Système de Gestion Hospitalière Localisée</p>
        <h1>Un portail hospitalier moderne, sécurisé et adapté à chaque service.</h1>
        <p class="hero-copy">
          Centralisez les consultations, les rendez-vous, la logistique et les communications internes avec une expérience fluide pour les visiteurs, les patients et le personnel.
        </p>
        <div class="hero-actions">
          <router-link class="btn btn-primary" to="/login">Accéder à la connexion</router-link>
          <router-link class="btn btn-secondary" to="/about">Découvrir le projet</router-link>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.home-shell { min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 24px; background: linear-gradient(135deg, #eff6ff, #f8fafc); }
.hero-card { max-width: 900px; width: 100%; background: white; border-radius: 24px; box-shadow: 0 20px 50px rgba(15, 23, 42, 0.12); padding: 40px; }
.eyebrow { color: #2563eb; font-weight: 700; text-transform: uppercase; letter-spacing: 0.25em; font-size: 0.8rem; }
.hero-card h1 { font-size: 2.2rem; margin: 10px 0 12px; color: #0f172a; }
.hero-copy { font-size: 1rem; color: #475569; line-height: 1.7; }
.hero-actions { display: flex; gap: 12px; margin-top: 22px; flex-wrap: wrap; }
.btn { padding: 12px 18px; border-radius: 999px; text-decoration: none; font-weight: 700; }
.btn-primary { background: #2563eb; color: white; }
.btn-secondary { background: #e2e8f0; color: #0f172a; }
</style>
