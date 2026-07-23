<template>
  <AppLayout>
    <div class="space-y-6 p-6">
      <header class="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p class="text-sm font-semibold uppercase tracking-[0.2em] text-indigo-700">Dossiers</p>
          <h1 class="mt-1 text-2xl font-bold text-slate-800">Patients</h1>
          <p class="mt-1 text-slate-500">Liste, création et consultation des dossiers.</p>
        </div>
        <button
          type="button"
          class="rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700"
          @click="showRegister = true"
        >
          + Nouveau patient
        </button>
      </header>

      <div v-if="errorMessage" class="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{{ errorMessage }}</div>
      <div v-if="successMessage" class="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{{ successMessage }}</div>

      <div class="grid gap-6 xl:grid-cols-[0.95fr_1.25fr]">
        <section class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <input
            v-model="search"
            type="search"
            placeholder="Rechercher nom, matricule…"
            class="mb-3 w-full rounded-xl border border-slate-300 px-3 py-2 text-sm"
          />
          <div v-if="loading" class="space-y-2">
            <div v-for="n in 6" :key="n" class="h-12 animate-pulse rounded-xl bg-slate-100" />
          </div>
          <ul v-else class="max-h-[32rem] space-y-1 overflow-y-auto">
            <li
              v-for="p in filteredPatients"
              :key="p.id"
              class="cursor-pointer rounded-xl px-3 py-2.5 text-sm transition hover:bg-indigo-50"
              :class="selectedId === p.id ? 'bg-indigo-50 ring-1 ring-indigo-200' : ''"
              @click="selectPatient(p.id)"
            >
              <p class="font-semibold text-slate-800">{{ p.nom }} {{ p.prenom }}</p>
              <p class="text-xs text-slate-500">{{ p.matricule }} · {{ p.telephone || 'Tél. N/A' }}</p>
            </li>
            <li v-if="!filteredPatients.length" class="px-3 py-6 text-center text-slate-500">Aucun patient.</li>
          </ul>
        </section>

        <section class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm min-h-[28rem]">
          <div v-if="!selectedId" class="flex h-full items-center justify-center text-slate-500">
            Sélectionnez un patient pour afficher le dossier.
          </div>
          <div v-else-if="detailLoading" class="space-y-3">
            <div class="h-8 w-48 animate-pulse rounded bg-slate-100" />
            <div class="h-40 animate-pulse rounded-xl bg-slate-100" />
          </div>
          <div v-else-if="patient.id">
            <div class="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h2 class="text-2xl font-bold text-slate-900">{{ patient.nom }} {{ patient.prenom }}</h2>
                <p class="text-slate-500">{{ patient.matricule }} · {{ patient.statut }}</p>
              </div>
              <div class="flex flex-wrap gap-2">
                <button type="button" class="rounded-xl bg-rose-600 px-3 py-2 text-xs font-semibold text-white" @click="downloadRecord('pdf')">
                  PDF dossier
                </button>
                <button type="button" class="rounded-xl bg-emerald-600 px-3 py-2 text-xs font-semibold text-white" @click="downloadRecord('excel')">
                  Excel dossier
                </button>
                <span class="rounded-full bg-indigo-100 px-3 py-1 text-xs font-bold text-indigo-700 self-center">
                  {{ patient.genre || 'Genre N/A' }}
                </span>
              </div>
            </div>

            <div class="mt-5 grid gap-4 sm:grid-cols-2">
              <div><p class="text-xs uppercase text-slate-400">Naissance</p><p class="font-medium">{{ patient.birth_date || '—' }}</p></div>
              <div><p class="text-xs uppercase text-slate-400">Téléphone</p><p class="font-medium">{{ patient.phone || '—' }}</p></div>
              <div><p class="text-xs uppercase text-slate-400">Email</p><p class="font-medium">{{ patient.email || '—' }}</p></div>
              <div><p class="text-xs uppercase text-slate-400">Groupe sanguin</p><p class="font-medium">{{ patient.groupe_sanguin || '—' }}</p></div>
              <div class="sm:col-span-2"><p class="text-xs uppercase text-slate-400">Allergies</p><p class="font-medium">{{ patient.allergies || '—' }}</p></div>
              <div class="sm:col-span-2"><p class="text-xs uppercase text-slate-400">Antécédents</p><p class="font-medium">{{ patient.antecedents || '—' }}</p></div>
            </div>

            <div v-if="patient.hospitalization" class="mt-5 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm">
              <p class="font-semibold text-amber-900">Hospitalisation active</p>
              <p class="text-amber-800">
                Lit {{ patient.hospitalization.bed }} · Chambre {{ patient.hospitalization.room }} ·
                {{ patient.hospitalization.service }} · Dr {{ patient.hospitalization.doctor }}
              </p>
              <p class="text-amber-700">{{ patient.hospitalization.reason }}</p>
            </div>

            <div class="mt-6">
              <h3 class="text-lg font-semibold text-slate-900">Historique médical</h3>
              <ul v-if="patient.consultations?.length" class="mt-3 divide-y divide-slate-100">
                <li v-for="c in patient.consultations" :key="c.id" class="py-3 text-sm">
                  <p class="text-xs text-slate-400">{{ formatDate(c.date) }} · Dr {{ c.doctor_username }}</p>
                  <p class="font-medium text-slate-800">{{ c.diagnosis || c.diagnostic }}</p>
                  <p class="text-slate-600">{{ c.symptoms }}</p>
                  <p v-if="c.prescription" class="text-slate-500">Prescription : {{ c.prescription }}</p>
                </li>
              </ul>
              <p v-else class="mt-3 text-sm italic text-slate-500">Aucune consultation enregistrée.</p>
            </div>
          </div>
        </section>
      </div>

      <!-- Modal register -->
      <div v-if="showRegister" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4" @click.self="showRegister = false">
        <form class="w-full max-w-lg space-y-3 rounded-2xl bg-white p-6 shadow-xl" @submit.prevent="registerPatient">
          <h2 class="text-xl font-bold text-slate-900">Nouveau dossier patient</h2>
          <div class="grid gap-3 sm:grid-cols-2">
            <input v-model="reg.first_name" required placeholder="Prénom" class="rounded-xl border border-slate-300 px-3 py-2 text-sm" />
            <input v-model="reg.last_name" required placeholder="Nom" class="rounded-xl border border-slate-300 px-3 py-2 text-sm" />
            <input v-model="reg.username" required placeholder="Identifiant" class="rounded-xl border border-slate-300 px-3 py-2 text-sm" />
            <input v-model="reg.password" required type="password" minlength="6" placeholder="Mot de passe (min 6)" class="rounded-xl border border-slate-300 px-3 py-2 text-sm" />
            <select v-model="reg.gender" required class="rounded-xl border border-slate-300 px-3 py-2 text-sm">
              <option value="" disabled>Genre</option>
              <option value="M">Masculin</option>
              <option value="F">Féminin</option>
              <option value="O">Autre</option>
            </select>
            <input v-model="reg.birth_date" required type="date" class="rounded-xl border border-slate-300 px-3 py-2 text-sm" />
            <input v-model="reg.phone" placeholder="Téléphone" class="rounded-xl border border-slate-300 px-3 py-2 text-sm sm:col-span-2" />
          </div>
          <p v-if="formError" class="text-sm text-rose-600">{{ formError }}</p>
          <div class="flex gap-3 pt-2">
            <button type="button" class="flex-1 rounded-xl border border-slate-300 py-2.5 text-sm font-semibold" @click="showRegister = false">Annuler</button>
            <button type="submit" class="flex-1 rounded-xl bg-indigo-600 py-2.5 text-sm font-semibold text-white" :disabled="saving">
              {{ saving ? 'Création…' : 'Créer' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import AppLayout from '@/components/AppLayout.vue';
import api from '@/api';
import { getApiBaseUrl } from '@/apiBase';

const route = useRoute();
const router = useRouter();
const patients = ref([]);
const patient = ref({});
const selectedId = ref(null);
const search = ref('');
const loading = ref(true);
const detailLoading = ref(false);
const showRegister = ref(false);
const saving = ref(false);
const errorMessage = ref('');
const successMessage = ref('');
const formError = ref('');

const reg = reactive({
  first_name: '',
  last_name: '',
  username: '',
  password: '',
  gender: '',
  birth_date: '',
  phone: '',
});

const filteredPatients = computed(() => {
  const q = search.value.trim().toLowerCase();
  if (!q) return patients.value;
  return patients.value.filter((p) =>
    `${p.nom} ${p.prenom} ${p.matricule}`.toLowerCase().includes(q),
  );
});

const apiBase = getApiBaseUrl();

const downloadRecord = async (format) => {
  if (!selectedId.value) return;
  try {
    const path = format === 'excel'
      ? `/clinical/patients/${selectedId.value}/record/excel`
      : `/clinical/patients/${selectedId.value}/record/pdf`;
    const response = await fetch(`${apiBase}${path}`, {
      headers: { Authorization: `Bearer ${localStorage.getItem('token') || ''}` },
    });
    if (!response.ok) throw new Error('Export indisponible');
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = format === 'excel' ? `dossier_${selectedId.value}.xlsx` : `dossier_${selectedId.value}.pdf`;
    a.click();
    URL.revokeObjectURL(url);
  } catch {
    errorMessage.value = 'Téléchargement impossible (installez reportlab/openpyxl côté serveur).';
  }
};

const apiError = (error, fallback) =>
  error?.response?.data?.detail || error?.response?.data?.message || fallback;

const formatDate = (value) => {
  try {
    return new Date(value).toLocaleString('fr-FR');
  } catch {
    return value;
  }
};

const fetchPatients = async () => {
  const response = await api.instance.get('/clinical/patients');
  patients.value = Array.isArray(response.data) ? response.data : [];
};

const selectPatient = async (id) => {
  selectedId.value = id;
  detailLoading.value = true;
  errorMessage.value = '';
  try {
    const response = await api.instance.get(`/clinical/patients/${id}`);
    patient.value = response.data || {};
    if (route.params.id != String(id)) {
      router.replace({ name: 'patient-detail', params: { id } });
    }
  } catch (error) {
    errorMessage.value = apiError(error, 'Impossible de charger le dossier.');
  } finally {
    detailLoading.value = false;
  }
};

const registerPatient = async () => {
  formError.value = '';
  saving.value = true;
  try {
    const response = await api.instance.post('/auth/register-patient/', {
      username: reg.username.trim(),
      password: reg.password,
      first_name: reg.first_name.trim(),
      last_name: reg.last_name.trim(),
      gender: reg.gender,
      birth_date: reg.birth_date,
      phone: reg.phone || null,
    });
    successMessage.value = response.data?.message || 'Patient créé.';
    showRegister.value = false;
    Object.assign(reg, {
      first_name: '', last_name: '', username: '', password: '', gender: '', birth_date: '', phone: '',
    });
    await fetchPatients();
    const newId = response.data?.patient?.id;
    if (newId) await selectPatient(newId);
  } catch (error) {
    formError.value = apiError(error, 'Création impossible.');
  } finally {
    saving.value = false;
  }
};

onMounted(async () => {
  loading.value = true;
  try {
    await fetchPatients();
    const idFromRoute = route.params.id ? Number(route.params.id) : null;
    if (idFromRoute) await selectPatient(idFromRoute);
  } catch (error) {
    errorMessage.value = apiError(error, 'Impossible de charger les patients.');
  } finally {
    loading.value = false;
  }
});
</script>
