<template>
  <AppLayout>
    <div class="p-6">
      <header class="flex justify-between items-center mb-6 flex-wrap gap-3">
        <div>
          <h1 class="text-2xl font-bold text-slate-800">Gestion du Personnel</h1>
          <p class="text-slate-500">Médecins, secrétaires et personnel hospitalier.</p>
        </div>
        <button
          type="button"
          class="bg-blue-600 text-white px-4 py-2 rounded-lg font-medium"
          :disabled="loading"
          @click="exportStaff"
        >
          Exporter CSV
        </button>
      </header>

      <div v-if="errorMessage" class="mb-4 rounded-lg bg-rose-50 text-rose-700 px-4 py-3 text-sm">{{ errorMessage }}</div>

      <div v-if="loading" class="text-slate-500 py-8 text-center">Chargement…</div>

      <div v-else class="bg-white rounded-xl shadow-sm border border-slate-200 p-6 overflow-x-auto">
        <table class="w-full text-left min-w-[520px]">
          <thead class="text-slate-400 text-sm border-b">
            <tr>
              <th class="pb-3">Nom</th>
              <th class="pb-3">Rôle</th>
              <th class="pb-3">Email</th>
              <th class="pb-3">Statut</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr v-for="member in staff" :key="member.id" class="text-slate-700">
              <td class="py-4 font-medium">{{ member.full_name }}</td>
              <td class="py-4">{{ roleLabel(member.role) }}</td>
              <td class="py-4">{{ member.email || '—' }}</td>
              <td class="py-4">
                <span :class="member.is_active ? 'text-emerald-600' : 'text-rose-600'">
                  {{ member.is_active ? 'Actif' : 'Inactif' }}
                </span>
              </td>
            </tr>
            <tr v-if="!staff.length">
              <td colspan="4" class="py-6 text-center text-slate-500">Aucun membre trouvé.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import AppLayout from '@/components/AppLayout.vue';
import api from '@/api';

const staff = ref([]);
const loading = ref(true);
const errorMessage = ref('');

const roleLabel = (role) => ({
  DG: 'Directeur Général',
  DOCTOR: 'Médecin',
  BIOLOGIST: 'Biologiste',
  SECRETARY_GENERAL: 'Secrétaire Générale',
  SECRETARY_SERVICE: 'Secrétaire de Service',
}[role] || role);

const fetchStaff = async () => {
  loading.value = true;
  errorMessage.value = '';
  try {
    const response = await api.instance.get('/finance/staff/');
    staff.value = Array.isArray(response.data) ? response.data : [];
  } catch (error) {
    errorMessage.value = error?.response?.data?.detail || 'Impossible de charger le personnel.';
    staff.value = [];
  } finally {
    loading.value = false;
  }
};

const exportStaff = async () => {
  try {
    await api.exportStaffCsv();
  } catch (error) {
    errorMessage.value = error?.response?.data?.detail || 'Export impossible.';
  }
};

onMounted(fetchStaff);
</script>
