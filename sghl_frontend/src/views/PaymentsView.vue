<template>
  <AppLayout>
    <div class="p-6 space-y-6">
      <div class="flex justify-between items-center">
        <h1 class="text-2xl font-bold text-slate-800">Gestion des Paiements</h1>
      </div>

      <div v-if="loading" class="text-center py-10">Chargement des paiements...</div>

      <div v-else class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="bg-slate-50 text-slate-400 border-b">
              <th class="p-4 uppercase text-xs font-semibold">Patient</th>
              <th class="p-4 uppercase text-xs font-semibold">Montant</th>
              <th class="p-4 uppercase text-xs font-semibold">Statut</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="invoice in invoices" :key="invoice.id" class="border-b last:border-0 hover:bg-slate-50 transition">
              <td class="p-4 font-medium">{{ invoice.patient?.username || 'N/A' }}</td>
              <td class="p-4">{{ invoice.total_amount }} FCFA</td>
              <td class="p-4">
                <span :class="['px-3 py-1 rounded-full text-xs font-bold', invoice.status === 'PAID' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700']">
                  {{ invoice.status }}
                </span>
              </td>
            </tr>
            <tr v-if="invoices.length === 0">
              <td colspan="3" class="p-8 text-center text-slate-500">Aucune facture enregistrée.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import api from '@/api';
import AppLayout from '@/components/AppLayout.vue';

const invoices = ref([]);
const loading = ref(true);

onMounted(async () => {
  try {
    const response = await api.instance.get('/clinical/invoices/'); // Ajusté pour utiliser ton instance api
    invoices.value = response.data;
  } catch (error) {
    console.error("Erreur lors de la récupération des factures :", error);
  } finally {
    loading.value = false;
  }
});
</script>