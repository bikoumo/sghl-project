<template>
  <AppLayout>
    <div class="min-h-screen bg-slate-50">
      <div class="bg-white border-b border-slate-200">
        <div class="max-w-7xl mx-auto px-6 py-8">
          <div class="flex justify-between items-center gap-4">
            <div>
              <h1 class="text-3xl font-bold text-slate-900">Tableau de Bord 🏥</h1>
              <p class="text-slate-600 mt-1">Bienvenue {{ userRole }} • SGHL</p>
            </div>
            <div class="text-right">
              <p class="text-sm text-slate-600">Profil actif</p>
              <p class="font-semibold text-slate-900">{{ roleLabel }}</p>
            </div>
          </div>
        </div>
      </div>

      <div class="max-w-7xl mx-auto px-6 py-8">
        <div v-if="loading" class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div v-for="index in 3" :key="index" class="bg-white rounded-xl shadow-sm border border-slate-200 p-6 animate-pulse">
            <div class="h-4 w-24 bg-slate-200 rounded mb-4"></div>
            <div class="h-8 w-16 bg-slate-200 rounded mb-2"></div>
            <div class="h-3 w-32 bg-slate-200 rounded"></div>
          </div>
        </div>

        <div v-else class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div v-for="card in summaryCards" :key="card.label" class="bg-white rounded-xl shadow-sm border border-slate-200 p-6 hover:shadow-md transition">
            <div class="flex justify-between items-start">
              <div>
                <p class="text-slate-600 text-sm font-medium">{{ card.label }}</p>
                <p class="text-4xl font-bold mt-2" :class="card.valueClass">{{ card.value }}</p>
                <p class="text-slate-500 text-xs mt-2">{{ card.helper }}</p>
              </div>
              <div :class="card.iconClass" class="p-3 rounded-lg">
                <span class="text-2xl">{{ card.icon }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6 mb-8">
          <h2 class="text-lg font-semibold text-slate-900 mb-4">Vue adaptée à votre rôle</h2>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div v-for="action in quickActions" :key="action.label" class="rounded-lg border border-slate-200 p-4">
              <div class="flex items-center gap-3 mb-2">
                <span class="text-2xl">{{ action.icon }}</span>
                <h3 class="font-semibold text-slate-900">{{ action.label }}</h3>
              </div>
              <p class="text-sm text-slate-600 mb-3">{{ action.description }}</p>
              <router-link :to="action.to" class="text-sm font-semibold text-blue-600">Ouvrir</router-link>
            </div>
          </div>
        </div>

        <div class="bg-blue-50 border border-blue-200 rounded-xl p-6">
          <div class="flex items-start gap-4">
            <span class="text-2xl">ℹ️</span>
            <div>
              <h3 class="font-semibold text-blue-900 mb-1">Accès service et communication</h3>
              <p class="text-sm text-blue-800">
                Les données sont filtrées selon votre rôle et votre service. Pour les urgences, utilisez le canal de chat interne et gardez les informations à jour en temps réel.
              </p>
            </div>
          </div>
        </div>
      </div>
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
});

onMounted(() => {
  const interval = setInterval(fetchStats, 30000);
  return () => clearInterval(interval);
});
</script>
