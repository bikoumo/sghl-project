<template>
  <AppLayout>
    <div class="p-6">
      <header class="mb-8">
        <h1 class="text-2xl font-bold text-slate-800">🏥 État des Lits</h1>
        <p class="text-slate-500">Gestion en temps réel de l'occupation des services.</p>
      </header>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div 
          v-for="bed in beds" 
          :key="bed.id" 
          :class="['p-6 rounded-xl shadow-sm border transition-all duration-300', bed.status === 'Libre' ? 'bg-emerald-50 border-emerald-200' : 'bg-red-50 border-red-200']"
        >
          <h3 class="text-lg font-bold text-slate-800">Lit {{ bed.number }}</h3>
          <p class="text-sm text-slate-600 mb-4">Service : {{ bed.service }}</p>
          
          <span :class="['px-3 py-1 rounded-full text-xs font-bold uppercase', bed.status === 'Libre' ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700']">
            {{ bed.status }}
          </span>
          
          <div class="mt-6">
            <button @click="toggleBedStatus(bed)" :class="['w-full py-2 rounded-lg font-semibold text-sm', bed.status === 'Libre' ? 'bg-emerald-600 text-white hover:bg-emerald-700' : 'bg-red-600 text-white hover:bg-red-700']">
              {{ bed.status === 'Libre' ? 'Admettre un patient' : 'Libérer le lit' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import AppLayout from '@/components/AppLayout.vue';
import api from '@/api';

const beds = ref([]);

const fetchBeds = async () => {
  try {
    // Appel API réel pour récupérer les lits
    const response = await api.instance.get('/clinical/beds/');
    beds.value = response.data;
  } catch (error) {
    console.error("Erreur chargement lits :", error);
    // Données de secours pour test si API non prête
    beds.value = [
      { id: 1, number: '101', service: 'Chirurgie', status: 'Libre' },
      { id: 2, number: '102', service: 'Médecine', status: 'Occupe' }
    ];
  }
};

const toggleBedStatus = async (bed) => {
  const newStatus = bed.status === 'Libre' ? 'Occupe' : 'Libre';
  try {
    await api.instance.patch(`/clinical/beds/${bed.id}/`, { status: newStatus });
    bed.status = newStatus;
  } catch (error) {
    alert("Impossible de modifier le statut du lit.");
  }
};

onMounted(fetchBeds);
</script>