<template>
  <AppLayout>
    <div class="space-y-6">
      <section class="dash-hero">
        <div class="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p class="dash-hero__eyebrow">Tableau de bord</p>
            <h1 class="mt-2 text-3xl font-bold text-white">
              <template v-if="['ADMIN', 'DG'].includes((userData.role || '').toUpperCase())">
                Bienvenue — vous avez l’accès complet à SGHL.
              </template>
              <template v-else>
                Bienvenue, {{ userRole }}
              </template>
            </h1>
            <p class="mt-2 max-w-2xl text-sm text-white/75">
              Vue synthétique de votre activité, des services concernés et des actions prioritaires.
            </p>
          </div>
          <div class="dash-hero__profile">
            <p class="font-semibold text-white">Profil actif</p>
            <p class="text-white/80">{{ roleLabel }}</p>
          </div>
        </div>
      </section>

      <div v-if="loading" class="grid gap-4 md:grid-cols-3">
        <div v-for="index in 3" :key="index" class="sghl-panel p-6 animate-pulse">
          <div class="h-4 w-24 rounded bg-slate-200"></div>
          <div class="mt-4 h-8 w-16 rounded bg-slate-200"></div>
          <div class="mt-3 h-3 w-32 rounded bg-slate-200"></div>
        </div>
      </div>

      <div v-else class="grid gap-4 md:grid-cols-3">
        <div v-for="card in summaryCards" :key="card.label" class="sghl-panel p-6 transition duration-200 hover:-translate-y-0.5">
          <div class="flex items-start justify-between gap-3">
            <div>
              <p class="text-sm font-medium text-[var(--sghl-muted)]">{{ card.label }}</p>
              <p class="mt-3 text-3xl font-semibold text-[var(--sghl-ink)]">{{ card.value }}</p>
              <p class="mt-2 text-xs text-[var(--sghl-muted)]">{{ card.helper }}</p>
            </div>
            <div class="dash-mark" :class="card.tone">{{ card.mark }}</div>
          </div>
        </div>
      </div>

      <div class="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <section class="sghl-panel p-6">
          <div class="mb-4 flex items-center justify-between">
            <h2 class="text-lg font-semibold">Accès rapide</h2>
            <span class="dash-badge">À jour</span>
          </div>
          <div class="grid gap-4 md:grid-cols-2">
            <div v-for="action in quickActions" :key="action.label" class="rounded-[12px] border border-[var(--sghl-line)] bg-[var(--sghl-mist)] p-4 transition hover:bg-white">
              <div>
                <h3 class="font-semibold text-[var(--sghl-ink)]">{{ action.label }}</h3>
                <p class="text-sm text-[var(--sghl-muted)]">{{ action.description }}</p>
              </div>
              <router-link :to="action.to" class="mt-4 inline-flex text-sm font-semibold text-[var(--sghl-lagoon)]">Ouvrir →</router-link>
            </div>
          </div>
        </section>

        <section class="sghl-panel p-6">
          <h2 class="text-lg font-semibold">Activités récentes</h2>
          <div class="mt-4 space-y-3">
            <div v-for="item in recentItems" :key="item.title" class="flex items-start gap-3 rounded-[12px] border border-[var(--sghl-line)] bg-[var(--sghl-mist)] p-3">
              <div class="mt-1 h-2 w-2 flex-shrink-0 rounded-sm bg-[var(--sghl-amber)]"></div>
              <div>
                <p class="text-sm font-semibold text-[var(--sghl-ink)]">{{ item.title }}</p>
                <p class="text-sm text-[var(--sghl-muted)]">{{ item.detail }}</p>
              </div>
            </div>
          </div>
        </section>
      </div>

      <section class="sghl-panel p-6" style="background: var(--sghl-mist)">
        <h3 class="font-semibold text-[var(--sghl-ink)]">Accès service et communication</h3>
        <p class="mt-1 text-sm text-[var(--sghl-muted)]">
          Les données sont filtrées selon votre rôle et votre service. Pour les urgences, utilisez le chat interne.
        </p>
        <div v-if="isPatient" class="mt-4 flex flex-wrap gap-3">
          <button type="button" class="sghl-btn sghl-btn-primary" @click="downloadMyRecord('pdf')">
            Télécharger mon dossier PDF
          </button>
          <button type="button" class="sghl-btn" style="background:#fff;border:1px solid var(--sghl-line);color:var(--sghl-ink)" @click="downloadMyRecord('excel')">
            Télécharger mon dossier Excel
          </button>
          <router-link to="/payments" class="sghl-btn" style="background:var(--sghl-teal-900);color:#fff;text-decoration:none">
            Mes factures / paiements
          </router-link>
        </div>
      </section>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import AppLayout from '@/components/AppLayout.vue';
import api from '@/api';
import { getApiBaseUrl } from '@/apiBase';

const router = useRouter();
const stats = ref({
  appointments_count: 0,
  hospitalized_count: 0,
  low_stock_count: 0,
  low_stock_items: []
});
const loading = ref(true);

const userData = computed(() => JSON.parse(localStorage.getItem('user') || '{}'));
const isPatient = computed(() => (userData.value.role || '').toUpperCase() === 'PATIENT');
const apiBase = getApiBaseUrl();

const downloadMyRecord = async (format) => {
  try {
    const path = format === 'excel' ? '/clinical/me/record/excel' : '/clinical/me/record/pdf';
    const response = await fetch(`${apiBase}${path}`, {
      headers: { Authorization: `Bearer ${localStorage.getItem('token') || ''}` },
    });
    if (!response.ok) throw new Error('Export indisponible');
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = format === 'excel' ? 'mon_dossier.xlsx' : 'mon_dossier.pdf';
    a.click();
    URL.revokeObjectURL(url);
  } catch (e) {
    console.error(e);
    alert('Téléchargement impossible pour le moment.');
  }
};

const userRole = computed(() => {
  const roleMap = {
    DG: 'Directeur Général',
    SECRETARY_GENERAL: 'Secrétaire Générale',
    SECRETARY_SERVICE: 'Secrétaire de Service',
    DOCTOR: 'Médecin',
    BIOLOGIST: 'Biologiste',
    PATIENT: 'Patient'
  };
  return roleMap[userData.value.role] || userData.value.role || 'Utilisateur';
});

const roleLabel = computed(() => {
  const role = (userData.value.role || '').toUpperCase();
  if (role === 'DOCTOR') return 'Médecin';
  if (role === 'PATIENT') return 'Patient';
  if (role === 'ADMIN' || role === 'DG') return 'Administrateur';
  if (role === 'BIOLOGIST') return 'Biologiste';
  if (role === 'SECRETARY' || role === 'SECRETARY_GENERAL' || role === 'SECRETARY_SERVICE') return 'Secrétaire';
  return 'Autre membre';
});

const summaryCards = computed(() => {
  const role = (userData.value.role || '').toUpperCase();
  if (role === 'DOCTOR') {
    return [
      { label: 'Consultations du jour', value: stats.value.appointments_count || 8, mark: 'C', tone: 'tone-lagoon', helper: 'Patients à suivre' },
      { label: 'Hospitalisations', value: stats.value.hospitalized_count || 3, mark: 'H', tone: 'tone-teal', helper: 'Admissions actives' },
      { label: 'Messages urgents', value: '3', mark: '!', tone: 'tone-amber', helper: 'Notifications internes' }
    ];
  }

  if (role === 'PATIENT') {
    return [
      { label: 'Rendez-vous à venir', value: '2', mark: 'R', tone: 'tone-lagoon', helper: 'Consultations à confirmer' },
      { label: 'Dossier médical', value: 'Actif', mark: 'D', tone: 'tone-teal', helper: 'Historique disponible' },
      { label: 'Messages', value: '1', mark: 'M', tone: 'tone-amber', helper: 'Communication interne' }
    ];
  }

  if (role === 'SECRETARY' || role === 'SECRETARY_GENERAL' || role === 'SECRETARY_SERVICE') {
    return [
      { label: 'Services suivis', value: '4', mark: 'S', tone: 'tone-lagoon', helper: 'Vue d’ensemble' },
      { label: 'Rendez-vous du jour', value: stats.value.appointments_count || 12, mark: 'R', tone: 'tone-teal', helper: 'Planning à jour' },
      { label: 'Alertes', value: stats.value.low_stock_count || 2, mark: '!', tone: 'tone-amber', helper: 'Interventions prioritaires' }
    ];
  }

  return [
    { label: 'Opérations', value: '24', mark: 'O', tone: 'tone-lagoon', helper: 'Actions en cours' },
    { label: 'Services actifs', value: '6', mark: 'S', tone: 'tone-teal', helper: 'Plateforme opérationnelle' },
    { label: 'Urgences', value: '1', mark: '!', tone: 'tone-amber', helper: 'Canal prioritaire' }
  ];
});

const quickActions = computed(() => {
  const role = (userData.value.role || '').toUpperCase();
  if (role === 'DOCTOR') {
    return [
      { label: 'Consultations', description: 'Consulter le dossier et enregistrer les soins.', to: '/consultation' },
      { label: 'Chat interne', description: 'Contacter rapidement les services concernés.', to: '/chat' }
    ];
  }
  if (role === 'PATIENT') {
    return [
      { label: 'Mes rendez-vous', description: 'Visualiser vos prochains rendez-vous.', to: '/appointments' },
      { label: 'Mes paiements', description: 'Payer par MTN, Airtel ou sur place.', to: '/payments' }
    ];
  }
  if (role === 'SECRETARY' || role === 'SECRETARY_GENERAL' || role === 'SECRETARY_SERVICE') {
    return [
      { label: 'Vue services', description: 'Surveiller les services assignés.', to: '/staff' },
      { label: 'Chat interne', description: 'Gérer les urgences et communications.', to: '/chat' }
    ];
  }
  return [
    { label: 'Gestion hospitalière', description: 'Centraliser les opérations administratives.', to: '/settings' },
    { label: 'Chat interne', description: 'Coordonner les équipes en cas d’urgence.', to: '/chat' }
  ];
});

const recentItems = computed(() => {
  const role = (userData.value.role || '').toUpperCase();
  if (role === 'DOCTOR') {
    return [
      { title: 'Consultation à venir', detail: '2 patients attendus aujourd’hui.' },
      { title: 'Urgence active', detail: 'Un message prioritaire a été reçu.' }
    ];
  }
  if (role === 'PATIENT') {
    return [
      { title: 'Rendez-vous confirmé', detail: 'Votre prochain passage est programmé.' },
      { title: 'Dossier médical', detail: 'Les derniers résultats sont disponibles.' }
    ];
  }
  return [
    { title: 'Planning du service', detail: 'Les rendez-vous du jour sont visibles.' },
    { title: 'Communication interne', detail: 'Les messages urgents sont traités rapidement.' }
  ];
});

const fetchStats = async () => {
  loading.value = true;
  try {
    const response = await api.instance.get('/clinical/stats/');
    stats.value = response.data;
  } catch (error) {
    console.error('Erreur chargement statistiques:', error);
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  const token = localStorage.getItem('token');
  const storedUser = JSON.parse(localStorage.getItem('user') || '{}');
  if (!token && !storedUser.token && !storedUser.access) {
    router.push('/login');
    return;
  }
  fetchStats();
  const interval = setInterval(fetchStats, 30000);
  return () => clearInterval(interval);
});
</script>

<style scoped>
.dash-hero {
  overflow: hidden;
  border-radius: var(--radius-lg);
  padding: 1.5rem;
  color: #fff;
  background:
    radial-gradient(ellipse at 90% 10%, rgba(212, 160, 23, 0.22), transparent 45%),
    linear-gradient(135deg, #032a34 0%, #054861 55%, #0f7a6b 140%);
  border: 1px solid rgba(232, 244, 241, 0.12);
  animation: sghl-fade-up 0.45s ease both;
}

.dash-hero__eyebrow {
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #d4a017;
}

.dash-hero__profile {
  border: 1px solid rgba(255, 255, 255, 0.14);
  background: rgba(255, 255, 255, 0.08);
  border-radius: var(--radius-md);
  padding: 0.85rem 1rem;
  font-size: 0.9rem;
}

.dash-mark {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 0.95rem;
}

.tone-lagoon { background: var(--sghl-lagoon-soft); color: var(--sghl-lagoon); }
.tone-teal { background: #d9ebe8; color: var(--sghl-teal-900); }
.tone-amber { background: var(--sghl-amber-soft); color: #8a6508; }

.dash-badge {
  border-radius: 6px;
  background: var(--sghl-lagoon-soft);
  color: var(--sghl-lagoon);
  padding: 0.25rem 0.65rem;
  font-size: 0.72rem;
  font-weight: 700;
}
</style>
