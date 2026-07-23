<template>
  <AppLayout>
    <div class="space-y-6 p-6">
      <header class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p class="text-sm font-semibold uppercase tracking-[0.2em] text-teal-700">Pharmacie</p>
          <h1 class="mt-1 text-2xl font-bold text-slate-800">Vente & stock</h1>
          <p class="mt-1 text-slate-500">
            Catalogue, panier patient, décrémentation FIFO des lots non périmés.
          </p>
        </div>
        <div class="flex flex-wrap gap-3 text-sm">
          <div class="rounded-xl border border-slate-200 bg-white px-4 py-2 font-semibold text-slate-700">
            Références : {{ medications.length }}
          </div>
          <div class="rounded-xl border border-amber-200 bg-amber-50 px-4 py-2 font-semibold text-amber-800">
            Stock bas : {{ lowStockCount }}
          </div>
          <div class="rounded-xl border border-teal-200 bg-teal-50 px-4 py-2 font-semibold text-teal-800">
            Panier : {{ cartCount }} art. · {{ cartTotal.toLocaleString('fr-FR') }} FCFA
          </div>
        </div>
      </header>

      <div v-if="errorMessage" class="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
        {{ errorMessage }}
      </div>
      <div v-if="successMessage" class="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
        {{ successMessage }}
      </div>

      <div class="grid gap-6 xl:grid-cols-[1.4fr_0.9fr]">
        <!-- Catalogue -->
        <section class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div class="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <h2 class="text-lg font-semibold text-slate-900">Catalogue</h2>
            <input
              v-model="search"
              type="search"
              placeholder="Rechercher nom ou code…"
              class="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm sm:max-w-xs"
            />
          </div>

          <div v-if="loading" class="space-y-3">
            <div v-for="n in 5" :key="n" class="h-14 animate-pulse rounded-xl bg-slate-100" />
          </div>

          <div v-else-if="!filteredMedications.length" class="py-10 text-center text-slate-500">
            Aucun médicament trouvé. Lancez le seed démo pour peupler le stock.
          </div>

          <div v-else class="max-h-[28rem] space-y-2 overflow-y-auto pr-1">
            <article
              v-for="med in filteredMedications"
              :key="med.id"
              class="flex flex-col gap-3 rounded-xl border border-slate-100 p-3 transition hover:border-teal-200 hover:bg-teal-50/40 sm:flex-row sm:items-center sm:justify-between"
            >
              <div>
                <p class="font-semibold text-slate-800">{{ med.name }}</p>
                <p class="text-xs text-slate-500">
                  {{ med.code }} · {{ Number(med.unit_price).toLocaleString('fr-FR') }} FCFA
                  <span v-if="med.next_expiry"> · péremption {{ med.next_expiry }}</span>
                </p>
              </div>
              <div class="flex items-center gap-2">
                <span
                  class="rounded-full px-2.5 py-1 text-xs font-bold"
                  :class="stockBadgeClass(med)"
                >
                  Stock {{ med.stock_quantity }}
                </span>
                <input
                  type="number"
                  min="1"
                  :max="med.stock_quantity || 1"
                  class="w-16 rounded-lg border border-slate-300 px-2 py-1.5 text-sm"
                  :value="qtyDraft[med.id] || 1"
                  :disabled="med.is_out_of_stock"
                  @input="qtyDraft[med.id] = Number($event.target.value) || 1"
                />
                <button
                  type="button"
                  class="rounded-lg bg-teal-600 px-3 py-1.5 text-sm font-semibold text-white hover:bg-teal-700 disabled:opacity-40"
                  :disabled="med.is_out_of_stock || actionLoading"
                  @click="addToCart(med)"
                >
                  Ajouter
                </button>
              </div>
            </article>
          </div>
        </section>

        <!-- Panier / vente -->
        <section class="space-y-5">
          <div class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 class="text-lg font-semibold text-slate-900">Vente patient</h2>

            <div class="mt-4 space-y-3">
              <div>
                <label class="mb-1 block text-sm font-semibold text-slate-700" for="patient">Patient</label>
                <select
                  id="patient"
                  v-model.number="patientId"
                  class="w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm"
                >
                  <option :value="0" disabled>Sélectionner…</option>
                  <option v-for="p in patients" :key="p.id" :value="p.id">
                    {{ p.nom }} {{ p.prenom }} ({{ p.matricule }})
                  </option>
                </select>
              </div>

              <label class="flex items-center gap-2 text-sm text-slate-700">
                <input v-model="markPaid" type="checkbox" class="rounded border-slate-300" />
                Marquer comme payé immédiatement
              </label>
            </div>

            <div v-if="!cart.length" class="mt-5 rounded-xl border border-dashed border-slate-300 p-6 text-center text-sm text-slate-500">
              Panier vide — ajoutez des médicaments depuis le catalogue.
            </div>

            <ul v-else class="mt-5 max-h-56 space-y-2 overflow-y-auto">
              <li
                v-for="line in cart"
                :key="line.medication_id"
                class="flex items-center justify-between gap-2 rounded-xl bg-slate-50 px-3 py-2 text-sm"
              >
                <div>
                  <p class="font-medium text-slate-800">{{ line.name }}</p>
                  <p class="text-xs text-slate-500">
                    {{ line.quantity }} × {{ line.unit_price.toLocaleString('fr-FR') }} FCFA
                  </p>
                </div>
                <div class="flex items-center gap-2">
                  <span class="font-semibold text-slate-800">
                    {{ (line.quantity * line.unit_price).toLocaleString('fr-FR') }}
                  </span>
                  <button type="button" class="text-rose-600 hover:underline" @click="removeFromCart(line.medication_id)">
                    Retirer
                  </button>
                </div>
              </li>
            </ul>

            <div class="mt-4 flex items-center justify-between border-t border-slate-100 pt-4">
              <span class="text-sm font-semibold text-slate-600">Total</span>
              <span class="text-xl font-bold text-slate-900">{{ cartTotal.toLocaleString('fr-FR') }} FCFA</span>
            </div>

            <button
              type="button"
              class="mt-4 w-full rounded-xl bg-teal-700 py-3 text-sm font-bold text-white hover:bg-teal-800 disabled:opacity-50"
              :disabled="!canCheckout || actionLoading"
              @click="checkout"
            >
              {{ actionLoading ? 'Traitement…' : 'Valider l’achat (déduire le stock)' }}
            </button>
          </div>

          <!-- Réappro -->
          <div class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 class="text-lg font-semibold text-slate-900">Réapprovisionner un lot</h2>
            <form class="mt-4 space-y-3" @submit.prevent="submitRestock">
              <select v-model.number="restock.medication_id" required class="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm">
                <option :value="0" disabled>Médicament…</option>
                <option v-for="m in medications" :key="m.id" :value="m.id">{{ m.name }}</option>
              </select>
              <input v-model="restock.batch_number" required placeholder="N° de lot" class="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm" />
              <div class="grid grid-cols-2 gap-3">
                <input v-model.number="restock.quantity" type="number" min="1" required placeholder="Quantité" class="rounded-xl border border-slate-300 px-3 py-2 text-sm" />
                <input v-model="restock.expiry_date" type="date" required class="rounded-xl border border-slate-300 px-3 py-2 text-sm" />
              </div>
              <button type="submit" class="w-full rounded-xl border border-teal-600 py-2.5 text-sm font-semibold text-teal-700 hover:bg-teal-50 disabled:opacity-50" :disabled="actionLoading">
                Ajouter au stock
              </button>
            </form>
          </div>

          <!-- Dernières ventes -->
          <div class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 class="text-lg font-semibold text-slate-900">Dernières ventes</h2>
            <ul v-if="invoices.length" class="mt-3 space-y-2 text-sm">
              <li v-for="inv in invoices" :key="inv.id" class="flex justify-between rounded-lg bg-slate-50 px-3 py-2">
                <span>#{{ inv.id }} · {{ inv.patient_username }}</span>
                <span class="font-semibold">{{ Number(inv.total_amount).toLocaleString('fr-FR') }} · {{ inv.status }}</span>
              </li>
            </ul>
            <p v-else class="mt-3 text-sm text-slate-500">Aucune vente récente.</p>
          </div>
        </section>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue';
import AppLayout from '@/components/AppLayout.vue';
import api from '@/api';

const medications = ref([]);
const patients = ref([]);
const invoices = ref([]);
const cart = ref([]);
const qtyDraft = reactive({});
const search = ref('');
const patientId = ref(0);
const markPaid = ref(false);
const loading = ref(true);
const actionLoading = ref(false);
const errorMessage = ref('');
const successMessage = ref('');
const restock = reactive({
  medication_id: 0,
  batch_number: '',
  quantity: 50,
  expiry_date: '',
});

const apiError = (error, fallback) =>
  error?.response?.data?.detail || error?.response?.data?.message || fallback;

const filteredMedications = computed(() => {
  const q = search.value.trim().toLowerCase();
  if (!q) return medications.value;
  return medications.value.filter(
    (m) => m.name.toLowerCase().includes(q) || (m.code || '').toLowerCase().includes(q),
  );
});

const lowStockCount = computed(() => medications.value.filter((m) => m.is_low_stock || m.stock_quantity < 10).length);
const cartCount = computed(() => cart.value.reduce((n, l) => n + l.quantity, 0));
const cartTotal = computed(() => cart.value.reduce((n, l) => n + l.quantity * l.unit_price, 0));
const canCheckout = computed(() => patientId.value > 0 && cart.value.length > 0);

const stockBadgeClass = (med) => {
  if (med.is_out_of_stock || med.stock_quantity <= 0) return 'bg-rose-100 text-rose-700';
  if (med.is_low_stock || med.stock_quantity < 10) return 'bg-amber-100 text-amber-800';
  return 'bg-emerald-100 text-emerald-700';
};

const fetchMedications = async () => {
  const response = await api.instance.get('/finance/medications/');
  medications.value = Array.isArray(response.data) ? response.data : [];
};

const fetchPatients = async () => {
  const response = await api.instance.get('/clinical/patients');
  patients.value = Array.isArray(response.data) ? response.data : [];
};

const fetchInvoices = async () => {
  try {
    const response = await api.instance.get('/finance/pharmacy/invoices');
    invoices.value = Array.isArray(response.data) ? response.data : [];
  } catch {
    invoices.value = [];
  }
};

const addToCart = (med) => {
  const qty = Math.max(1, Number(qtyDraft[med.id] || 1));
  if (qty > med.stock_quantity) {
    errorMessage.value = `Stock insuffisant pour ${med.name} (max ${med.stock_quantity}).`;
    return;
  }
  errorMessage.value = '';
  const existing = cart.value.find((l) => l.medication_id === med.id);
  if (existing) {
    const next = existing.quantity + qty;
    if (next > med.stock_quantity) {
      errorMessage.value = `Stock insuffisant pour ${med.name}.`;
      return;
    }
    existing.quantity = next;
  } else {
    cart.value.push({
      medication_id: med.id,
      name: med.name,
      unit_price: Number(med.unit_price),
      quantity: qty,
    });
  }
};

const removeFromCart = (medicationId) => {
  cart.value = cart.value.filter((l) => l.medication_id !== medicationId);
};

const checkout = async () => {
  if (!canCheckout.value) return;
  actionLoading.value = true;
  errorMessage.value = '';
  successMessage.value = '';
  try {
    const response = await api.instance.post('/finance/pharmacy/purchase', {
      patient_id: patientId.value,
      mark_paid: markPaid.value,
      items: cart.value.map((l) => ({
        medication_id: l.medication_id,
        quantity: l.quantity,
      })),
    });
    const data = response.data;
    successMessage.value = data.message || 'Achat enregistré.';
    cart.value = [];
    await Promise.all([fetchMedications(), fetchInvoices()]);
  } catch (error) {
    errorMessage.value = apiError(error, 'Échec de la vente.');
  } finally {
    actionLoading.value = false;
  }
};

const submitRestock = async () => {
  if (!restock.medication_id || !restock.batch_number || !restock.expiry_date) {
    errorMessage.value = 'Complétez le formulaire de réapprovisionnement.';
    return;
  }
  actionLoading.value = true;
  errorMessage.value = '';
  successMessage.value = '';
  try {
    const response = await api.instance.post('/finance/pharmacy/restock', {
      medication_id: restock.medication_id,
      batch_number: restock.batch_number.trim(),
      quantity: restock.quantity,
      expiry_date: restock.expiry_date,
    });
    successMessage.value = response.data.message || 'Stock mis à jour.';
    restock.batch_number = '';
    await fetchMedications();
  } catch (error) {
    errorMessage.value = apiError(error, 'Échec du réapprovisionnement.');
  } finally {
    actionLoading.value = false;
  }
};

onMounted(async () => {
  loading.value = true;
  try {
    await Promise.all([fetchMedications(), fetchPatients(), fetchInvoices()]);
  } catch (error) {
    errorMessage.value = apiError(error, 'Impossible de charger la pharmacie.');
  } finally {
    loading.value = false;
  }
});
</script>
