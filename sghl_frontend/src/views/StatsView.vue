<template>
  <AppLayout>
    <div class="p-6 space-y-6">
      <header>
        <h1 class="text-2xl font-bold text-slate-800">📊 Tableau de Bord Global</h1>
        <p class="text-slate-500">Vue d'ensemble de l'activité hospitalière</p>
      </header>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
          <h3 class="text-slate-400 text-sm font-semibold uppercase">Consultations</h3>
          <p class="text-3xl font-bold text-blue-600 mt-2">{{ stats.consultations }}</p>
        </div>
        
        <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
          <h3 class="text-slate-400 text-sm font-semibold uppercase">Lits Occupés</h3>
          <p class="text-3xl font-bold text-amber-600 mt-2">{{ stats.beds_occupied }} / {{ stats.beds_total }}</p>
        </div>
        
        <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
          <h3 class="text-slate-400 text-sm font-semibold uppercase">Urgences</h3>
          <p class="text-3xl font-bold text-red-600 mt-2">{{ stats.emergencies }}</p>
        </div>
      </div>
      
      </div>
  </AppLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import AppLayout from '@/components/AppLayout.vue';
import api from '@/api';

const stats = ref({
  consultations: 0,
  beds_occupied: 0,
  beds_total: 0,
  emergencies: 0
});

const fetchStats = async () => {
  try {
    // Appel à ton endpoint de statistiques
    const response = await api.instance.get('/clinical/stats/');
    stats.value = response.data;
  } catch (error) {
    console.error("Erreur chargement statistiques :", error);
  }
};

onMounted(fetchStats);
</script>