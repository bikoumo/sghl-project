<template>
  <AppLayout>
    <div class="p-6 space-y-6">
      <div class="flex items-center justify-between">
        <router-link to="/dashboard" class="text-slate-500 hover:text-slate-800 font-medium">
          &larr; Retour au tableau de bord
        </router-link>
        <span class="bg-blue-100 text-blue-700 px-4 py-1 rounded-full text-sm font-bold">
          Matricule: #{{ patient.matricule }}
        </span>
      </div>

      <header class="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
        <h1 class="text-3xl font-bold text-slate-800">{{ patient.nom }} {{ patient.prenom }}</h1>
        <p class="text-slate-500">Dossier médical complet</p>
      </header>

      <div class="flex gap-4 border-b border-slate-200">
        <button 
          @click="activeTab = 'info'" 
          :class="['pb-3 px-2 font-semibold transition', activeTab === 'info' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-slate-400']"
        >
          Infos Personnelles
        </button>
        <button 
          @click="activeTab = 'history'" 
          :class="['pb-3 px-2 font-semibold transition', activeTab === 'history' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-slate-400']"
        >
          Historique Médical
        </button>
      </div>

      <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200 min-h-[300px]">
        <div v-if="activeTab === 'info'" class="space-y-6">
          <div class="grid grid-cols-2 gap-4">
            <div><label class="text-slate-400 text-sm">Date de naissance</label><p class="font-medium">{{ patient.birth_date }}</p></div>
            <div><label class="text-slate-400 text-sm">Téléphone</label><p class="font-medium">{{ patient.phone }}</p></div>
          </div>

          <div class="mt-8 border-t pt-6">
            <h3 class="text-lg font-bold text-slate-800 mb-4">Évolution & Visualisation</h3>
            <div class="bg-slate-50 p-6 rounded-lg text-center border-2 border-dashed border-slate-200">
              <p class="text-slate-400 italic">Espace réservé pour les courbes de croissance / étapes cliniques</p>
              <div class="mt-4 flex justify-center gap-4">
                 <div class="w-32 h-32 bg-slate-200 rounded flex items-center justify-center">Image 1</div>
                 <div class="w-32 h-32 bg-slate-200 rounded flex items-center justify-center">Image 2</div>
              </div>
            </div>
          </div>
        </div>

        <div v-if="activeTab === 'history'" class="space-y-4">
          <ul v-if="patient.consultations && patient.consultations.length > 0" class="divide-y divide-slate-100">
            <li v-for="consult in patient.consultations" :key="consult.id" class="py-4">
              <p class="text-sm text-slate-400">{{ consult.date }}</p>
              <p class="font-medium text-slate-800">Diagnostic : {{ consult.diagnostic }}</p>
            </li>
          </ul>
          <p v-else class="text-slate-500 italic">Aucun historique de consultation disponible.</p>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import AppLayout from '@/components/AppLayout.vue';
import api from '@/api';

const route = useRoute();
const activeTab = ref('info');
const patient = ref({ nom: '', prenom: '', matricule: '', birth_date: '', phone: '', consultations: [] });

const fetchPatientDetails = async () => {
  try {
    const id = route.params.id;
    const response = await api.instance.get(`/clinical/patients/${id}/`);
    patient.value = response.data;
  } catch (error) {
    console.error("Erreur chargement patient :", error);
  }
};

onMounted(fetchPatientDetails);
</script>