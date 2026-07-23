<template>
  <div class="shell">
    <aside class="sidebar">
      <div class="sidebar__brand">
        <SghlLogo size="md" light tagline="Portail hospitalier" />
      </div>

      <div class="sidebar__role">{{ roleLabel }}</div>

      <nav class="sidebar__nav" aria-label="Navigation principale">
        <router-link :to="dashboardRoute" class="nav-link">
          <span class="nav-ico" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none"><path d="M4 11.5 12 4l8 7.5V20a1 1 0 0 1-1 1h-5v-6H10v6H5a1 1 0 0 1-1-1v-8.5Z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/></svg>
          </span>
          Tableau de bord
        </router-link>

        <p v-if="isAdmin" class="nav-section">Gestion</p>

        <router-link v-if="canAccessPatients" to="/patients" class="nav-link">
          <span class="nav-ico" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none"><path d="M8 7h8M8 12h8M8 17h5M6 3h12a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>
          </span>
          Dossiers patients
        </router-link>

        <router-link v-if="canAccessLaboratory" to="/laboratory" class="nav-link">
          <span class="nav-ico" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none"><path d="M9 3v7l-4.5 8.2A2 2 0 0 0 6.3 21h11.4a2 2 0 0 0 1.8-2.8L15 10V3M8 3h8" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </span>
          Laboratoire
        </router-link>

        <router-link v-if="canAccessPharmacy" to="/pharmacy" class="nav-link">
          <span class="nav-ico" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none"><path d="M9 8h6M12 5v6m-6.5 4.5a5.5 5.5 0 1 0 11 0v-1h-11v1Z" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>
          </span>
          Pharmacie & stocks
        </router-link>

        <router-link v-if="canAccessPayments" to="/payments" class="nav-link">
          <span class="nav-ico" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none"><rect x="3" y="6" width="18" height="12" rx="2" stroke="currentColor" stroke-width="1.6"/><path d="M3 10h18M7 14h4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>
          </span>
          Facturation
        </router-link>

        <router-link v-if="canAccessVisitors" to="/visitors" class="nav-link">
          <span class="nav-ico" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none"><path d="M12 21s7-5.4 7-11a7 7 0 1 0-14 0c0 5.6 7 11 7 11Z" stroke="currentColor" stroke-width="1.6"/><circle cx="12" cy="10" r="2.5" stroke="currentColor" stroke-width="1.6"/></svg>
          </span>
          Visites
        </router-link>

        <router-link v-if="canAccessPediatrie" to="/pediatrie" class="nav-link">
          <span class="nav-ico" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none"><circle cx="12" cy="8" r="3.2" stroke="currentColor" stroke-width="1.6"/><path d="M5 20c1.2-3.2 3.7-5 7-5s5.8 1.8 7 5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>
          </span>
          Pédiatrie
        </router-link>

        <router-link v-if="canAccessStaff" to="/staff" class="nav-link">
          <span class="nav-ico" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none"><path d="M16 11a3.5 3.5 0 1 0-7 0 3.5 3.5 0 0 0 7 0ZM4 20c1.3-3.4 4-5 8-5s6.7 1.6 8 5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>
          </span>
          Personnel
        </router-link>

        <p class="nav-section">Quotidien</p>

        <router-link to="/appointments" class="nav-link">
          <span class="nav-ico" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none"><rect x="3.5" y="5" width="17" height="15" rx="2" stroke="currentColor" stroke-width="1.6"/><path d="M8 3v4M16 3v4M3.5 10h17" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>
          </span>
          Rendez-vous
        </router-link>

        <router-link v-if="isAdmin" to="/chat" class="nav-link">
          <span class="nav-ico" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none"><path d="M5 18.5 6.2 15A7.5 7.5 0 1 1 9 19.4L5 18.5Z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/></svg>
          </span>
          Chat interne
        </router-link>

        <router-link to="/profile" class="nav-link">
          <span class="nav-ico" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none"><circle cx="12" cy="8" r="3.2" stroke="currentColor" stroke-width="1.6"/><path d="M5.5 19.5c1.2-3.2 3.6-4.8 6.5-4.8s5.3 1.6 6.5 4.8" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>
          </span>
          Profil
        </router-link>

        <p class="nav-section">Parcours patient</p>
        <div class="steps">
          <router-link
            v-for="step in visibleSteps"
            :key="step.n"
            :to="step.route"
            class="step-chip"
          >
            <span class="step-num">{{ step.n }}</span>
            <span>{{ step.label }}</span>
          </router-link>
        </div>
      </nav>

      <div class="sidebar__foot">
        <button type="button" class="logout-btn" @click="logout">Déconnexion</button>
      </div>
    </aside>

    <main class="content">
      <div class="content__inner sghl-page">
        <slot />
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useRouter } from 'vue-router';
import SghlLogo from '@/components/SghlLogo.vue';

const router = useRouter();
const userData = computed(() => JSON.parse(localStorage.getItem('user') || '{}'));

const isAdmin = computed(() => {
  const role = (userData.value.role || '').toUpperCase();
  return role === 'ADMIN' || role === 'DG';
});

const canAccessLaboratory = computed(() => {
  const role = normalizeRole(userData.value.role);
  return ['ADMIN', 'DOCTOR', 'SECRETARY'].includes(role);
});

const canAccessPediatrie = computed(() => {
  const role = normalizeRole(userData.value.role);
  return ['ADMIN', 'DOCTOR', 'SECRETARY'].includes(role);
});

const canAccessVisitors = computed(() => {
  const role = normalizeRole(userData.value.role);
  return ['ADMIN', 'SECRETARY'].includes(role);
});

const canAccessStaff = computed(() => {
  const role = normalizeRole(userData.value.role);
  return ['ADMIN', 'SECRETARY'].includes(role);
});

const canAccessPharmacy = computed(() => {
  const role = normalizeRole(userData.value.role);
  return ['ADMIN', 'DOCTOR', 'SECRETARY'].includes(role);
});

const canAccessPatients = computed(() => {
  const role = normalizeRole(userData.value.role);
  return ['ADMIN', 'DOCTOR', 'SECRETARY'].includes(role);
});

const canAccessPayments = computed(() => {
  const role = normalizeRole(userData.value.role);
  return ['ADMIN', 'DOCTOR', 'SECRETARY', 'PATIENT'].includes(role);
});

const roleLabel = computed(() => {
  const role = (userData.value.role || '').toUpperCase();
  if (role === 'ADMIN' || role === 'DG') return 'Directeur Général';
  if (role === 'SECRETARY_GENERAL') return 'Secrétaire Générale';
  if (role === 'SECRETARY_SERVICE') return 'Secrétaire de Service';
  if (role === 'DOCTOR') return 'Médecin';
  if (role === 'BIOLOGIST') return 'Biologiste';
  if (role === 'PATIENT') return 'Patient';
  return role || 'Utilisateur';
});

const dashboardRoute = computed(() => {
  const role = (userData.value.role || '').toUpperCase();
  if (role === 'ADMIN' || role === 'DG') return '/dashboard/admin';
  if (role === 'DOCTOR' || role === 'BIOLOGIST') return '/dashboard/doctor';
  if (role === 'SECRETARY_GENERAL' || role === 'SECRETARY_SERVICE' || role === 'SECRETARY') return '/dashboard/secretary';
  if (role === 'PATIENT') return '/dashboard/patient';
  return '/dashboard';
});

const logout = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  router.push('/login');
};

function normalizeRole(role) {
  const r = (role || '').toUpperCase();
  if (['DG', 'ADMIN'].includes(r)) return 'ADMIN';
  if (['SECRETARY', 'SECRETARY_GENERAL', 'SECRETARY_SERVICE'].includes(r)) return 'SECRETARY';
  if (['DOCTOR', 'BIOLOGIST', 'OTHER'].includes(r)) return 'DOCTOR';
  if (r === 'PATIENT') return 'PATIENT';
  return null;
}

const stepMap = {
  1: { route: '/beds', label: 'Admission' },
  2: { route: '/consultation', label: 'Consultation' },
  3: { route: '/laboratory', label: 'Laboratoire' },
  4: { route: '/laboratory', label: 'Imagerie' },
  5: { route: '/pediatrie', label: 'Pédiatrie' },
  6: { route: '/maternity', label: 'Maternité' },
  7: { route: '/pharmacy', label: 'Pharmacie' },
  8: { route: '/beds', label: 'Hospitalisation' },
  9: { route: '/visitors', label: 'Visiteurs' },
  10: { route: '/payments', label: 'Facturation' },
  11: { route: '/staff', label: 'Staff' },
  12: { route: '/chat', label: 'Chat' },
  13: { route: '/stats', label: 'Statistiques' },
  14: { route: '/settings', label: 'Paramètres' },
  15: { route: '/patients', label: 'Dossier' },
  16: { route: '/stats', label: 'Rapports' },
};

const canAccessStep = (step) => {
  const role = normalizeRole(userData.value.role);
  if (role === 'ADMIN') return true;
  if (role === 'DOCTOR') return [2, 3, 4, 5, 6, 7, 8, 10, 12, 15].includes(step);
  if (role === 'SECRETARY') return [1, 2, 3, 5, 6, 7, 9, 10, 11, 15, 16].includes(step);
  if (role === 'PATIENT') return [2, 10, 15].includes(step);
  return false;
};

const visibleSteps = computed(() =>
  Object.entries(stepMap)
    .map(([n, meta]) => ({ n: Number(n), ...meta }))
    .filter((s) => canAccessStep(s.n)),
);
</script>

<style scoped>
.shell {
  display: flex;
  min-height: 100vh;
  background: var(--sghl-surface);
}

.sidebar {
  width: 280px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  color: #f5fbf9;
  background:
    linear-gradient(180deg, rgba(15, 122, 107, 0.18), transparent 28%),
    linear-gradient(165deg, #032a34 0%, #054861 100%);
  border-right: 1px solid rgba(232, 244, 241, 0.08);
}

.sidebar__brand {
  padding: 1.35rem 1.25rem 1rem;
  border-bottom: 1px solid rgba(232, 244, 241, 0.1);
}

.sidebar__role {
  margin: 0.9rem 1.25rem 0.35rem;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgba(212, 160, 23, 0.95);
}

.sidebar__nav {
  flex: 1;
  overflow-y: auto;
  padding: 0.5rem 0.75rem 1rem;
}

.nav-section {
  margin: 1rem 0.65rem 0.4rem;
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: rgba(232, 244, 241, 0.45);
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  padding: 0.7rem 0.8rem;
  margin-bottom: 0.15rem;
  border-radius: var(--radius-sm);
  text-decoration: none;
  color: rgba(232, 244, 241, 0.82);
  font-size: 0.9rem;
  font-weight: 550;
  transition: background 0.18s ease, color 0.18s ease;
}

.nav-link:hover {
  background: rgba(232, 244, 241, 0.08);
  color: #fff;
}

.nav-link.router-link-active {
  background: rgba(15, 122, 107, 0.35);
  color: #fff;
  box-shadow: inset 3px 0 0 var(--sghl-amber);
}

.nav-ico {
  width: 1.25rem;
  height: 1.25rem;
  display: inline-flex;
  flex-shrink: 0;
}

.nav-ico svg {
  width: 100%;
  height: 100%;
}

.steps {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.4rem;
  padding: 0.25rem 0.35rem;
}

.step-chip {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.4rem 0.45rem;
  border-radius: 6px;
  text-decoration: none;
  font-size: 0.72rem;
  color: rgba(232, 244, 241, 0.75);
  background: rgba(255, 255, 255, 0.04);
  transition: background 0.15s ease;
}

.step-chip:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.step-num {
  width: 1.2rem;
  height: 1.2rem;
  border-radius: 4px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.65rem;
  font-weight: 700;
  background: rgba(212, 160, 23, 0.2);
  color: #f7edd0;
  flex-shrink: 0;
}

.sidebar__foot {
  padding: 1rem 1.1rem 1.2rem;
  border-top: 1px solid rgba(232, 244, 241, 0.1);
}

.logout-btn {
  width: 100%;
  border: 1px solid rgba(232, 244, 241, 0.2);
  background: rgba(15, 122, 107, 0.45);
  color: #fff;
  padding: 0.7rem 1rem;
  border-radius: var(--radius-sm);
  font-weight: 650;
  cursor: pointer;
  transition: background 0.18s ease;
}

.logout-btn:hover {
  background: rgba(15, 122, 107, 0.7);
}

.content {
  flex: 1;
  min-width: 0;
  overflow-y: auto;
  background:
    radial-gradient(circle at top left, rgba(15, 122, 107, 0.07), transparent 32%),
    radial-gradient(circle at 90% 10%, rgba(212, 160, 23, 0.06), transparent 28%),
    var(--sghl-surface);
}

.content__inner {
  padding: 1.5rem clamp(1rem, 2.5vw, 2rem);
  max-width: 1280px;
}

@media (max-width: 900px) {
  .shell {
    flex-direction: column;
  }

  .sidebar {
    width: 100%;
    max-height: none;
  }

  .sidebar__nav {
    max-height: 42vh;
  }
}
</style>
