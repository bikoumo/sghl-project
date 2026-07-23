
<template>
  <AppLayout>
    <div class="space-y-6 p-6">
      <header class="rounded-[24px] border border-slate-200 bg-white p-6 shadow-sm">
        <p class="text-sm font-semibold uppercase tracking-[0.24em] text-emerald-600">Visite & Facturation</p>
        <h1 class="mt-2 text-3xl font-bold text-slate-900">Recherche patient & création facture</h1>
      </header>

      <div v-if="errorMessage" class="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{{ errorMessage }}</div>
      <div v-if="successMessage" class="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{{ successMessage }}</div>

      <!-- Barre de recherche -->
      <div class="rounded-[24px] border border-slate-200 bg-white p-5 shadow-sm">
        <label class="mb-2 block text-sm font-semibold text-slate-700">Rechercher un patient</label>
        <div class="flex gap-3">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Nom, prénom, email, matricule ou téléphone..."
            class="flex-1 rounded-xl border border-slate-300 px-4 py-2.5 text-sm"
            @input="debouncedSearch"
          />
        </div>

        <!-- Résultats recherche -->
        <div v-if="searchResults.length > 0" class="mt-4 space-y-2">
          <div
            v-for="p in searchResults"
            :key="p.id"
            class="flex cursor-pointer items-center justify-between rounded-xl border border-slate-100 px-4 py-3 hover:bg-emerald-50"
            @click="selectPatient(p)"
          >
            <div>
              <p class="font-medium text-slate-900">{{ p.prenom }} {{ p.nom }}</p>
              <p class="text-xs text-slate-500">{{ p.matricule }} — {{ p.telephone }} — {{ p.statut }}</p>
            </div>
            <span class="text-xs font-semibold text-emerald-600">Sélectionner</span>
          </div>
        </div>
        <p v-else-if="searchQuery.length >= 2" class="mt-3 text-sm text-slate-500">Aucun patient trouvé.</p>

        <!-- Patient sélectionné -->
        <div v-if="selectedPatient" class="mt-4 rounded-xl bg-emerald-50 p-4">
          <p class="font-semibold text-emerald-800">Patient sélectionné</p>
          <p class="text-sm text-emerald-700">{{ selectedPatient.prenom }} {{ selectedPatient.nom }} ({{ selectedPatient.matricule }})</p>
        </div>
      </div>

      <!-- Formulaire création facture -->
      <div v-if="selectedPatient" class="rounded-[24px] border border-slate-200 bg-white p-6 shadow-sm">
        <h2 class="text-lg font-bold text-slate-900">Nouvelle facture pour {{ selectedPatient.prenom }} {{ selectedPatient.nom }}</h2>

        <div class="mt-4">
          <label class="mb-1 block text-sm font-semibold text-slate-700">Libellé</label>
          <input v-model="invoiceForm.label" type="text" placeholder="Ex: Consultation, soins..." class="w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm" />
        </div>

        <div class="mt-4">
          <div class="flex items-center justify-between">
            <label class="mb-1 block text-sm font-semibold text-slate-700">Lignes de facture</label>
            <button type="button" class="text-sm font-semibold text-emerald-600 hover:underline" @click="addLine">+ Ajouter une ligne</button>
          </div>
          <div v-for="(line, idx) in invoiceForm.lines" :key="idx" class="mt-2 flex gap-2">
            <input v-model="line.label" type="text" placeholder="Libellé" class="flex-1 rounded-xl border border-slate-300 px-3 py-2 text-sm" />
            <input v-model.number="line.quantity" type="number" min="1" placeholder="Qté" class="w-20 rounded-xl border border-slate-300 px-3 py-2 text-sm" />
            <input v-model.number="line.unit_price" type="number" min="0" step="100" placeholder="P.U." class="w-28 rounded-xl border border-slate-300 px-3 py-2 text-sm" />
            <span class="flex items-center text-sm font-medium text-slate-600">{{ (line.quantity * line.unit_price).toLocaleString('fr-FR') }} F</span>
            <button type="button" class="text-rose-500 hover:text-rose-700" @click="removeLine(idx)">✕</button>
          </div>
        </div>

        <div class="mt-4 flex items-center justify-between border-t border-slate-100 pt-4">
          <p class="text-lg font-bold text-slate-900">Total : {{ invoiceTotal.toLocaleString('fr-FR') }} FCFA</p>
          <button
            type="button"
            class="rounded-xl bg-emerald-600 px-6 py-2.5 text-sm font-semibold text-white hover:bg-emerald-700"
            :disabled="creatingInvoice"
            @click="submitInvoice"
          >
            {{ creatingInvoice ? 'Création...' : 'Créer la facture' }}
          </button>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue';
import { useRouter } from 'vue-router';
import api from '@/api';
import AppLayout from '@/components/AppLayout.vue';

const router = useRouter();
const searchQuery = ref('');
const searchResults = ref([]);
const selectedPatient = ref(null);
const errorMessage = ref('');
const successMessage = ref('');
const creatingInvoice = ref(false);

const user = JSON.parse(localStorage.getItem('user') || '{}');
const role = (user.role || '').toUpperCase();

const invoiceForm = reactive({
  label: 'Facture de soins',
  lines: [
    { label: 'Consultation médicale', quantity: 1, unit_price: 15000 },
  ],
});

let debounceTimer = null;

const debouncedSearch = () => {
  clearTimeout(debounceTimer);
  if (searchQuery.value.length < 1) {
    searchResults.value = [];
    return;
  }
  debounceTimer = setTimeout(performSearch, 400);
};

const performSearch = async () => {
  try {
    const res = await api.searchPatients(searchQuery.value);
    searchResults.value = Array.isArray(res.data) ? res.data : [];
  } catch {
    searchResults.value = [];
  }
};

const selectPatient = (patient) => {
  selectedPatient.value = patient;
  searchResults.value = [];
  searchQuery.value = '';
};

const addLine = () => {
  invoiceForm.lines.push({ label: '', quantity: 1, unit_price: 0 });
};

const removeLine = (idx) => {
  if (invoiceForm.lines.length > 1) {
    invoiceForm.lines.splice(idx, 1);
  }
};

const invoiceTotal = computed(() => {
  return invoiceForm.lines.reduce((sum, line) => sum + (line.quantity || 0) * (line.unit_price || 0), 0);
});

const submitInvoice = async () => {
  if (!selectedPatient.value) return;
  if (invoiceForm.lines.length === 0) {
    errorMessage.value = 'Ajoutez au moins une ligne.';
    return;
  }
  creatingInvoice.value = true;
  errorMessage.value = '';
  successMessage.value = '';
  try {
    const payload = {
      patient_id: selectedPatient.value.id,
      label: invoiceForm.label || 'Facture',
      lines: invoiceForm.lines.map(l => ({
        label: l.label || 'Prestation',
        quantity: l.quantity || 1,
        unit_price: l.unit_price || 0,
      })),
    };
    const res = await api.createInvoice(payload);
    successMessage.value = `Facture #${res.data.id} créée — ${res.data.total_amount.toLocaleString('fr-FR')} FCFA`;
    // Reset
    selectedPatient.value = null;
    invoiceForm.label = 'Facture de soins';
    invoiceForm.lines = [{ label: 'Consultation médicale', quantity: 1, unit_price: 15000 }];
  } catch (error) {
    errorMessage.value = error?.response?.data?.detail || 'Erreur de création.';
  } finally {
    creatingInvoice.value = false;
  }
};

onMounted(() => {
  const allowed = ['ADMIN', 'DG', 'SECRETARY_GENERAL', 'SECRETARY_SERVICE', 'DOCTOR'];
  if (!allowed.includes(role)) {
    router.push('/dashboard');
  }
});
</script>

