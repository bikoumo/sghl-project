<template>
  <AppLayout>
    <div class="p-6 max-w-2xl">
      <h1 class="text-2xl font-bold text-slate-800 mb-6">Paramètres</h1>

      <div v-if="successMessage" class="mb-4 rounded-lg bg-emerald-50 text-emerald-700 px-4 py-3 text-sm">{{ successMessage }}</div>

      <form class="bg-white p-6 rounded-xl shadow-sm border border-slate-200 space-y-6" @submit.prevent="saveSettings">
        <div>
          <label class="block font-medium text-slate-700">Nom de l'établissement</label>
          <input v-model="settings.establishmentName" type="text" class="w-full border p-2 rounded mt-1" required />
        </div>
        <div>
          <label class="block font-medium text-slate-700">Seuil d'alerte des rendez-vous (jours)</label>
          <input v-model.number="settings.appointmentAlertDays" type="number" min="1" max="30" class="w-full border p-2 rounded mt-1" required />
        </div>
        <div>
          <label class="block font-medium text-slate-700">Email de notification</label>
          <input v-model="settings.notificationEmail" type="email" class="w-full border p-2 rounded mt-1" placeholder="contact@hopital.com" />
        </div>
        <button type="submit" class="bg-green-600 text-white px-6 py-2 rounded-lg font-bold">Enregistrer les modifications</button>
      </form>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import AppLayout from '@/components/AppLayout.vue';

const STORAGE_KEY = 'sghl_settings';
const settings = ref({
  establishmentName: 'SGHL Pointe-Noire',
  appointmentAlertDays: 3,
  notificationEmail: '',
});
const successMessage = ref('');

onMounted(() => {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
    settings.value = { ...settings.value, ...saved };
  } catch { /* ignore */ }
});

const saveSettings = () => {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(settings.value));
  successMessage.value = 'Paramètres enregistrés localement.';
  setTimeout(() => { successMessage.value = ''; }, 3000);
};
</script>
