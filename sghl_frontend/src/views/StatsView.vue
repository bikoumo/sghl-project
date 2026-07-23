<template>
  <AppLayout>
    <div class="space-y-6 p-6">
      <header class="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p class="text-sm font-semibold uppercase tracking-[0.2em] text-blue-700">Rapports</p>
          <h1 class="mt-1 text-2xl font-bold text-slate-800">Tableau de bord & exports</h1>
          <p class="mt-1 text-slate-500">Activité clinique du {{ stats.date || '…' }}</p>
        </div>
        <div class="flex flex-wrap gap-2">
          <button type="button" class="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold" :disabled="loading" @click="fetchAll">
            Actualiser
          </button>
          <button
            type="button"
            class="rounded-xl bg-slate-800 px-4 py-2 text-sm font-semibold text-white"
            :disabled="loading"
            @click="exportCsv"
          >
            Export factures CSV
          </button>
        </div>
      </header>

      <div v-if="errorMessage" class="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
        {{ errorMessage }}
      </div>

      <div class="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <div v-for="card in cards" :key="card.label" class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <h3 class="text-xs font-semibold uppercase tracking-wide text-slate-400">{{ card.label }}</h3>
          <p class="mt-2 text-3xl font-bold" :class="card.color">{{ card.value }}</p>
          <p class="mt-1 text-xs text-slate-500">{{ card.hint }}</p>
        </div>
      </div>

      <div class="grid gap-6 xl:grid-cols-2">
        <section class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 class="text-lg font-semibold text-slate-900">Hospitalisations actives</h2>
          <div v-if="loading" class="mt-4 h-24 animate-pulse rounded-xl bg-slate-100" />
          <ul v-else-if="hospitalized.length" class="mt-4 divide-y divide-slate-100">
            <li v-for="bed in hospitalized" :key="bed.id" class="py-3 text-sm">
              <p class="font-semibold text-slate-800">{{ bed.patient_name }} · Lit {{ bed.number }}</p>
              <p class="text-slate-500">{{ bed.service_name }} · Dr {{ bed.doctor_name || '—' }}</p>
              <p class="text-slate-500 line-clamp-1">{{ bed.reason }}</p>
            </li>
          </ul>
          <p v-else class="mt-4 text-sm text-slate-500">Aucune hospitalisation active.</p>
        </section>

        <section class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 class="text-lg font-semibold text-slate-900">Actions rapides</h2>
          <div class="mt-4 grid gap-3 sm:grid-cols-2">
            <router-link to="/consultation" class="rounded-xl border border-slate-200 px-4 py-3 text-sm font-semibold hover:bg-slate-50">Consultation</router-link>
            <router-link to="/beds" class="rounded-xl border border-slate-200 px-4 py-3 text-sm font-semibold hover:bg-slate-50">Admission / Lits</router-link>
            <router-link to="/appointments" class="rounded-xl border border-slate-200 px-4 py-3 text-sm font-semibold hover:bg-slate-50">Rendez-vous</router-link>
            <router-link to="/pharmacy" class="rounded-xl border border-slate-200 px-4 py-3 text-sm font-semibold hover:bg-slate-50">Pharmacie</router-link>
            <router-link to="/payments" class="rounded-xl border border-slate-200 px-4 py-3 text-sm font-semibold hover:bg-slate-50">Facturation</router-link>
            <router-link to="/patients" class="rounded-xl border border-slate-200 px-4 py-3 text-sm font-semibold hover:bg-slate-50">Dossiers patients</router-link>
          </div>
          <p class="mt-5 text-xs text-slate-500">
            Occupancy : {{ stats.beds_occupied || 0 }} / {{ stats.beds_total || 0 }} lits ·
            Stock bas : {{ stats.low_stock_count || 0 }} ·
            Factures en attente : {{ stats.invoices_pending || 0 }}
          </p>
        </section>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import AppLayout from '@/components/AppLayout.vue';
import api from '@/api';

const stats = ref({
  date: '',
  consultations: 0,
  beds_occupied: 0,
  beds_total: 0,
  emergencies: 0,
  low_stock_count: 0,
  appointments_count: 0,
  hospitalized_count: 0,
  patients_count: 0,
  invoices_pending: 0,
});
const hospitalized = ref([]);
const loading = ref(true);
const errorMessage = ref('');

const cards = computed(() => [
  { label: 'Consultations du jour', value: stats.value.consultations || 0, color: 'text-blue-600', hint: 'Actes médicaux enregistrés' },
  { label: 'Lits occupés', value: `${stats.value.beds_occupied || 0} / ${stats.value.beds_total || 0}`, color: 'text-amber-600', hint: 'Hospitalisations actives' },
  { label: 'RDV confirmés', value: stats.value.appointments_count || 0, color: 'text-emerald-600', hint: 'Agenda du jour' },
  { label: 'Urgences / alertes', value: stats.value.emergencies || 0, color: 'text-rose-600', hint: 'Service URG' },
]);

const fetchAll = async () => {
  loading.value = true;
  errorMessage.value = '';
  try {
    const [statsRes, bedsRes] = await Promise.all([
      api.instance.get('/clinical/stats/'),
      api.instance.get('/clinical/beds/'),
    ]);
    stats.value = { ...stats.value, ...(statsRes.data || {}) };
    const beds = Array.isArray(bedsRes.data) ? bedsRes.data : [];
    hospitalized.value = beds.filter((b) => b.is_occupied);
  } catch (error) {
    errorMessage.value = error?.response?.data?.detail || 'Impossible de charger les rapports.';
  } finally {
    loading.value = false;
  }
};

const exportCsv = async () => {
  try {
    await api.exportInvoicesCsv();
  } catch (error) {
    errorMessage.value = error?.response?.data?.detail || 'Export CSV impossible.';
  }
};

onMounted(fetchAll);
</script>
