<template>
  <AppLayout>
    <div class="space-y-6">
      <section class="overflow-hidden rounded-[24px] border border-slate-200 bg-gradient-to-br from-[#0b1727] via-[#11263d] to-[#1b3d5f] p-6 text-white shadow-sm">
        <div class="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p class="text-sm font-semibold uppercase tracking-[0.24em] text-emerald-300">Tableau de bord</p>
            <h1 class="mt-2 text-3xl font-bold">Bienvenue {{ userRole }}</h1>
            <p class="mt-2 max-w-2xl text-sm text-slate-300">Vue synthétique de votre activité, des services concernés et des actions prioritaires à réaliser.</p>
          </div>
          <div class="rounded-2xl border border-white/10 bg-white/10 px-4 py-3 text-sm text-slate-100 backdrop-blur">
            <p class="font-semibold text-white">Profil actif</p>
            <p>{{ roleLabel }}</p>
          </div>
        </div>
      </section>

      <div v-if="loading" class="grid gap-4 md:grid-cols-3">
        <div v-for="index in 3" :key="index" class="rounded-[20px] border border-slate-200 bg-white p-6 shadow-sm animate-pulse">
          <div class="h-4 w-24 rounded bg-slate-200"></div>
          <div class="mt-4 h-8 w-16 rounded bg-slate-200"></div>
          <div class="mt-3 h-3 w-32 rounded bg-slate-200"></div>
        </div>
      </div>

      <div v-else class="grid gap-4 md:grid-cols-3">
        <div v-for="card in summaryCards" :key="card.label" class="rounded-[20px] border border-slate-200 bg-white p-6 shadow-sm transition duration-200 hover:-translate-y-1 hover:shadow-lg">
          <div class="flex items-start justify-between gap-3">
            <div>
              <p class="text-sm font-medium text-slate-500">{{ card.label }}</p>
              <p class="mt-3 text-3xl font-semibold text-slate-900">{{ card.value }}</p>
              <p class="mt-2 text-xs text-slate-500">{{ card.helper }}</p>
            </div>
            <div :class="card.iconClass" class="rounded-2xl p-3 text-2xl">{{ card.icon }}</div>
          </div>
        </div>
      </div>

      <div class="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <section class="rounded-[24px] border border-slate-200 bg-white p-6 shadow-sm">
          <div class="mb-4 flex items-center justify-between">
            <h2 class="text-lg font-semibold text-slate-900">Accès rapide</h2>
            <span class="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">À jour</span>
          </div>
          <div class="grid gap-4 md:grid-cols-2">
            <div v-for="action in quickActions" :key="action.label" class="rounded-2xl border border-slate-200 bg-slate-50 p-4 transition duration-200 hover:-translate-y-1 hover:bg-white">
              <div class="flex items-center gap-3">
                <div class="rounded-xl bg-white p-2 text-xl shadow-sm">{{ action.icon }}</div>
                <div>
                  <h3 class="font-semibold text-slate-900">{{ action.label }}</h3>
                  <p class="text-sm text-slate-600">{{ action.description }}</p>
                </div>
              </div>
              <router-link :to="action.to" class="mt-4 inline-flex text-sm font-semibold text-emerald-700">Ouvrir →</router-link>
            </div>
          </div>
        </section>

        <section class="rounded-[24px] border border-slate-200 bg-white p-6 shadow-sm">
          <h2 class="text-lg font-semibold text-slate-900">Activités récentes</h2>
          <div class="mt-4 space-y-3">
            <div v-for="item in recentItems" :key="item.title" class="flex items-start gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-3 transition hover:bg-white">
              <div class="rounded-full bg-emerald-100 px-2 py-1 text-sm">•</div>
              <div>
                <p class="text-sm font-semibold text-slate-900">{{ item.title }}</p>
                <p class="text-sm text-slate-500">{{ item.detail }}</p>
              </div>
            </div>
          </div>
        </section>
      </div>

      <section class="rounded-[24px] border border-slate-200 bg-[#eef5ff] p-6 shadow-sm">
        <div class="flex items-start gap-3">
          <span class="text-2xl">ℹ️</span>
          <div>
            <h3 class="font-semibold text-slate-900">Accès service et communication</h3>
            <p class="mt-1 text-sm text-slate-700">Les données sont filtrées selon votre rôle et votre service. Pour les urgences, utilisez le canal de chat interne et gardez les informations à jour en temps réel.</p>
          </div>
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

const router = useRouter();
const stats = ref({
  appointments_count: 0,
  hospitalized_count: 0,
  low_stock_count: 0,
  low_stock_items: []
});
const loading = ref(true);

const userData = computed(() => JSON.parse(localStorage.getItem('user') || '{}'));

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
  if (role === 'ADMIN') return 'Administrateur';
  if (role === 'SECRETARY' || role === 'SECRETARY_GENERAL' || role === 'SECRETARY_SERVICE') return 'Secrétaire';
  return 'Autre membre';
});

const summaryCards = computed(() => {
  const role = (userData.value.role || '').toUpperCase();
  if (role === 'DOCTOR') {
    return [
      { label: 'Consultations du jour', value: stats.value.appointments_count || 8, valueClass: 'text-blue-600', iconClass: 'bg-blue-100', icon: '🩺', helper: 'Patients à suivre' },
      { label: 'Hospitalisations', value: stats.value.hospitalized_count || 3, valueClass: 'text-emerald-600', iconClass: 'bg-emerald-100', icon: '🏥', helper: 'Admissions actives' },
      { label: 'Messages urgents', value: '3', valueClass: 'text-amber-600', iconClass: 'bg-amber-100', icon: '🚨', helper: 'Notifications internes' }
    ];
  }

  if (role === 'PATIENT') {
    return [
      { label: 'Rendez-vous à venir', value: '2', valueClass: 'text-blue-600', iconClass: 'bg-blue-100', icon: '📅', helper: 'Consultations à confirmer' },
      { label: 'Dossier médical', value: 'Actif', valueClass: 'text-emerald-600', iconClass: 'bg-emerald-100', icon: '🧾', helper: 'Historique disponible' },
      { label: 'Messages', value: '1', valueClass: 'text-amber-600', iconClass: 'bg-amber-100', icon: '💬', helper: 'Communication interne' }
    ];
  }

  if (role === 'SECRETARY' || role === 'SECRETARY_GENERAL' || role === 'SECRETARY_SERVICE') {
    return [
      { label: 'Services suivis', value: '4', valueClass: 'text-blue-600', iconClass: 'bg-blue-100', icon: '🏢', helper: 'Vue d’ensemble' },
      { label: 'Rendez-vous du jour', value: stats.value.appointments_count || 12, valueClass: 'text-emerald-600', iconClass: 'bg-emerald-100', icon: '📋', helper: 'Planning à jour' },
      { label: 'Alertes', value: stats.value.low_stock_count || 2, valueClass: 'text-amber-600', iconClass: 'bg-amber-100', icon: '⚠️', helper: 'Interventions prioritaires' }
    ];
  }

  return [
    { label: 'Opérations', value: '24', valueClass: 'text-blue-600', iconClass: 'bg-blue-100', icon: '⚙️', helper: 'Actions en cours' },
    { label: 'Services actifs', value: '6', valueClass: 'text-emerald-600', iconClass: 'bg-emerald-100', icon: '🏥', helper: 'Plateforme opérationnelle' },
    { label: 'Urgences', value: '1', valueClass: 'text-amber-600', iconClass: 'bg-amber-100', icon: '🚨', helper: 'Canal prioritaire' }
  ];
});

const quickActions = computed(() => {
  const role = (userData.value.role || '').toUpperCase();
  if (role === 'DOCTOR') {
    return [
      { label: 'Consultations', icon: '🩺', description: 'Consulter le dossier et enregistrer les soins.', to: '/consultation' },
      { label: 'Chat interne', icon: '💬', description: 'Contacter rapidement les services concernés.', to: '/chat' }
    ];
  }
  if (role === 'PATIENT') {
    return [
      { label: 'Mes rendez-vous', icon: '📅', description: 'Visualiser vos prochains rendez-vous.', to: '/appointments' },
      { label: 'Chat interne', icon: '💬', description: 'Contacter l’équipe hospitalière.', to: '/chat' }
    ];
  }
  if (role === 'SECRETARY' || role === 'SECRETARY_GENERAL' || role === 'SECRETARY_SERVICE') {
    return [
      { label: 'Vue services', icon: '🏢', description: 'Surveiller les services assignés.', to: '/staff' },
      { label: 'Chat interne', icon: '💬', description: 'Gérer les urgences et communications.', to: '/chat' }
    ];
  }
  return [
    { label: 'Gestion hospitalière', icon: '⚙️', description: 'Centraliser les opérations administratives.', to: '/settings' },
    { label: 'Chat interne', icon: '💬', description: 'Coordonner les équipes en cas d’urgence.', to: '/chat' }
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
  const storedUser = JSON.parse(localStorage.getItem('user') || '{}');
  if (!storedUser.token && !storedUser.access) {
    router.push('/login');
    return;
  }
  fetchStats();
  const interval = setInterval(fetchStats, 30000);
  return () => clearInterval(interval);
});
</script>
