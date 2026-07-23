<template>
  <AppLayout>
    <div class="space-y-6 p-6">
      <header class="rounded-[24px] border border-slate-200 bg-white p-6 shadow-sm">
        <p class="text-sm font-semibold uppercase tracking-[0.24em] text-emerald-600">Facturation</p>
        <h1 class="mt-2 text-3xl font-bold text-slate-900">Paiements & reçus</h1>
        <p class="mt-1 text-slate-600">
          Sur place (espèces), MTN Mobile Money, Airtel Money ou Carte bancaire.
        </p>
      </header>

      <div v-if="errorMessage" class="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{{ errorMessage }}</div>
      <div v-if="successMessage" class="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{{ successMessage }}</div>

      <div class="flex flex-wrap items-center justify-between gap-3">
        <div class="grid flex-1 gap-4 md:grid-cols-3">
          <div class="rounded-[20px] border border-slate-200 bg-white p-5 shadow-sm">
            <p class="text-sm text-slate-500">Total factures</p>
            <p class="mt-3 text-3xl font-semibold text-slate-900">{{ invoices.length }}</p>
          </div>
          <div class="rounded-[20px] border border-slate-200 bg-white p-5 shadow-sm">
            <p class="text-sm text-slate-500">Payées</p>
            <p class="mt-3 text-3xl font-semibold text-emerald-600">{{ paidCount }}</p>
          </div>
          <div class="rounded-[20px] border border-slate-200 bg-white p-5 shadow-sm">
            <p class="text-sm text-slate-500">En attente</p>
            <p class="mt-3 text-3xl font-semibold text-amber-600">{{ pendingCount }}</p>
          </div>
        </div>
        <router-link
          to="/visit"
          class="rounded-xl bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-blue-700"
        >
          + Créer une facture
        </router-link>
      </div>

      <div v-if="loading" class="rounded-[24px] border border-slate-200 bg-white p-10 text-center">Chargement...</div>

      <div v-else class="overflow-hidden rounded-[24px] border border-slate-200 bg-white shadow-sm">
        <table class="w-full text-left">
          <thead>
            <tr class="bg-slate-50 text-xs uppercase tracking-wide text-slate-600">
              <th class="px-5 py-4">#</th>
              <th class="px-5 py-4">Libellé</th>
              <th class="px-5 py-4">Patient</th>
              <th class="px-5 py-4">Montant</th>
              <th class="px-5 py-4">Statut</th>
              <th class="px-5 py-4">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="invoice in invoices" :key="invoice.id" class="border-t border-slate-100 hover:bg-slate-50">
              <td class="px-5 py-4 text-slate-500">{{ invoice.id }}</td>
              <td class="px-5 py-4">{{ invoice.label || 'Consultation' }}</td>
              <td class="px-5 py-4 font-medium">{{ invoice.patient?.username || invoice.patient_username || 'N/A' }}</td>
              <td class="px-5 py-4">{{ Number(invoice.total_amount).toLocaleString('fr-FR') }} FCFA</td>
              <td class="px-5 py-4">
                <span
                  :class="isPaid(invoice) ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'"
                  class="rounded-full px-3 py-1 text-xs font-semibold"
                >
                  {{ isPaid(invoice) ? 'Payée' : 'En attente' }}
                </span>
              </td>
              <td class="px-5 py-4">
                <div class="flex flex-wrap gap-2">
                  <button
                    v-if="!isPaid(invoice)"
                    type="button"
                    class="text-sm font-semibold text-emerald-700 hover:underline"
                    @click="openPay(invoice)"
                  >
                    Payer
                  </button>
                  <button type="button" class="text-sm font-semibold text-slate-600 hover:underline" @click="downloadPdf(invoice.id)">
                    PDF
                  </button>
                  <button
                    v-if="invoice.consultation_id"
                    type="button"
                    class="text-sm font-semibold text-indigo-700 hover:underline"
                    @click="downloadReceipt(invoice.consultation_id)"
                  >
                    Reçu consult.
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="!invoices.length">
              <td colspan="6" class="px-5 py-8 text-center text-slate-500">Aucune facture.</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Modal paiement -->
      <div v-if="payInvoice" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4" @click.self="payInvoice = null">
        <form class="w-full max-w-md space-y-4 rounded-2xl bg-white p-6 shadow-xl" @submit.prevent="submitPayment">
          <h2 class="text-xl font-bold text-slate-900">Payer la facture #{{ payInvoice.id }}</h2>
          <p class="text-sm text-slate-600">
            Reste à payer :
            <strong>{{ Number(payInvoice.remaining ?? payInvoice.total_amount).toLocaleString('fr-FR') }} FCFA</strong>
          </p>

          <div>
            <label class="mb-1 block text-sm font-semibold">Mode de paiement</label>
<select v-model="payForm.method" required class="w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm">
              <option value="CASH">Sur place (espèces)</option>
              <option value="MTN">MTN Mobile Money</option>
              <option value="AIRTEL">Airtel Money</option>
              <option value="CARD">Carte bancaire</option>
            </select>
          </div>

          <div v-if="payForm.method === 'MTN' || payForm.method === 'AIRTEL'">
            <label class="mb-1 block text-sm font-semibold">Numéro téléphone {{ payForm.method }}</label>
            <input
              v-model="payForm.phone"
              type="tel"
              required
              placeholder="Ex: 06XXXXXXX"
              class="w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm"
            />
          </div>

          <p v-if="formError" class="text-sm text-rose-600">{{ formError }}</p>

          <div class="flex gap-3">
            <button type="button" class="flex-1 rounded-xl border border-slate-300 py-2.5 text-sm font-semibold" @click="payInvoice = null">Annuler</button>
            <button type="submit" class="flex-1 rounded-xl bg-emerald-600 py-2.5 text-sm font-semibold text-white" :disabled="paying">
              {{ paying ? 'Traitement…' : 'Confirmer' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue';
import { useRouter } from 'vue-router';
import api from '@/api';
import { getApiBaseUrl } from '@/apiBase';
import AppLayout from '@/components/AppLayout.vue';

const router = useRouter();
const invoices = ref([]);
const loading = ref(true);
const paying = ref(false);
const errorMessage = ref('');
const successMessage = ref('');
const formError = ref('');
const payInvoice = ref(null);
const payForm = reactive({ method: 'CASH', phone: '' });

const user = JSON.parse(localStorage.getItem('user') || '{}');
const role = (user.role || '').toUpperCase();
const apiBase = getApiBaseUrl();

const isPaid = (invoice) => ['PAID'].includes(String(invoice.status || '').toUpperCase());
const paidCount = computed(() => invoices.value.filter((i) => isPaid(i)).length);
const pendingCount = computed(() => invoices.value.filter((i) => !isPaid(i)).length);

const authHeaders = () => ({
  Authorization: `Bearer ${localStorage.getItem('token') || ''}`,
});

const loadInvoices = async () => {
  const response = await api.instance.get('/clinical/invoices/');
  invoices.value = Array.isArray(response.data) ? response.data : [];
};

const openPay = (invoice) => {
  payInvoice.value = invoice;
  payForm.method = 'CASH';
  payForm.phone = '';
  formError.value = '';
};

const submitPayment = async () => {
  formError.value = '';
  paying.value = true;
  try {
    const payload = { method: payForm.method };
    if (payForm.method === 'MTN' || payForm.method === 'AIRTEL') {
      payload.phone = payForm.phone.trim();
    }
    const response = await api.instance.post(`/clinical/invoices/${payInvoice.value.id}/pay`, payload);
    successMessage.value = `${response.data.message} Réf: ${response.data.transaction_ref}`;
    payInvoice.value = null;
    await loadInvoices();
  } catch (error) {
    formError.value = error?.response?.data?.detail || 'Paiement impossible.';
  } finally {
    paying.value = false;
  }
};

const downloadPdf = async (invoiceId) => {
  try {
    const response = await fetch(`${apiBase}/clinical/invoices/${invoiceId}/pdf`, { headers: authHeaders() });
    if (!response.ok) throw new Error('PDF indisponible');
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `facture_${invoiceId}.pdf`;
    a.click();
    URL.revokeObjectURL(url);
  } catch {
    errorMessage.value = 'Impossible de télécharger la facture PDF (reportlab requis).';
  }
};

const downloadReceipt = async (consultationId) => {
  try {
    const response = await fetch(`${apiBase}/clinical/consultations/${consultationId}/receipt/pdf`, { headers: authHeaders() });
    if (!response.ok) throw new Error('Reçu indisponible');
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `recu_consultation_${consultationId}.pdf`;
    a.click();
    URL.revokeObjectURL(url);
  } catch {
    errorMessage.value = 'Impossible de télécharger le reçu.';
  }
};

onMounted(async () => {
  const allowed = ['ADMIN', 'DG', 'SECRETARY_GENERAL', 'SECRETARY_SERVICE', 'PATIENT', 'DOCTOR'];
  if (!allowed.includes(role)) {
    router.push('/dashboard');
    return;
  }
  try {
    await loadInvoices();
  } catch (error) {
    errorMessage.value = error?.response?.data?.detail || 'Erreur de chargement.';
  } finally {
    loading.value = false;
  }
});
</script>
