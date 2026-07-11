<template>
  <AppLayout>
    <div class="space-y-6">
      <header class="rounded-[24px] border border-slate-200 bg-white p-6 shadow-sm">
        <p class="text-sm font-semibold uppercase tracking-[0.24em] text-emerald-600">Facturation</p>
        <h1 class="mt-2 text-3xl font-bold text-slate-900">Gestion des paiements</h1>
        <p class="mt-1 text-slate-600">Synthèse des factures et de leur statut de paiement.</p>
      </header>

      <div class="grid gap-4 md:grid-cols-3">
        <div class="rounded-[20px] border border-slate-200 bg-white p-5 shadow-sm transition duration-200 hover:-translate-y-1 hover:shadow-md">
          <p class="text-sm text-slate-500">Total factures</p>
          <p class="mt-3 text-3xl font-semibold text-slate-900">{{ invoices.length }}</p>
        </div>
        <div class="rounded-[20px] border border-slate-200 bg-white p-5 shadow-sm transition duration-200 hover:-translate-y-1 hover:shadow-md">
          <p class="text-sm text-slate-500">Payées</p>
          <p class="mt-3 text-3xl font-semibold text-emerald-600">{{ paidCount }}</p>
        </div>
        <div class="rounded-[20px] border border-slate-200 bg-white p-5 shadow-sm transition duration-200 hover:-translate-y-1 hover:shadow-md">
          <p class="text-sm text-slate-500">En attente</p>
          <p class="mt-3 text-3xl font-semibold text-amber-600">{{ pendingCount }}</p>
        </div>
      </div>

      <div v-if="loading" class="rounded-[24px] border border-slate-200 bg-white p-10 text-center text-slate-600">Chargement des paiements...</div>

      <div v-else class="overflow-hidden rounded-[24px] border border-slate-200 bg-white shadow-sm">
        <table class="w-full text-left">
          <thead>
            <tr class="bg-slate-50 text-xs uppercase tracking-wide text-slate-600">
              <th class="px-5 py-4">Patient</th>
              <th class="px-5 py-4">Montant</th>
              <th class="px-5 py-4">Statut</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="invoice in invoices" :key="invoice.id" class="border-t border-slate-100 transition hover:bg-slate-50">
              <td class="px-5 py-4 font-medium text-slate-900">{{ invoice.patient?.username || 'N/A' }}</td>
              <td class="px-5 py-4 text-slate-700">{{ invoice.total_amount }} FCFA</td>
              <td class="px-5 py-4">
                <span :class="invoice.status === 'PAID' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'" class="rounded-full px-3 py-1 text-xs font-semibold">
                  {{ invoice.status === 'PAID' ? 'Payée' : 'En attente' }}
                </span>
              </td>
            </tr>
            <tr v-if="invoices.length === 0">
              <td colspan="3" class="px-5 py-8 text-center text-slate-600">Aucune facture enregistrée.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import api from '@/api';
import AppLayout from '@/components/AppLayout.vue';

const invoices = ref([]);
const loading = ref(true);

const paidCount = computed(() => invoices.value.filter((invoice) => invoice.status === 'PAID').length);
const pendingCount = computed(() => invoices.value.filter((invoice) => invoice.status !== 'PAID').length);

onMounted(async () => {
  try {
    const response = await api.instance.get('/clinical/invoices/');
    invoices.value = Array.isArray(response.data) ? response.data : response.data?.invoices || [];
  } catch (error) {
    console.error('Erreur lors de la récupération des factures :', error);
  } finally {
    loading.value = false;
  }
});
</script>