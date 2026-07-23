<template>
  <AppLayout>
    <div class="mat-page">
      <header class="mat-hero">
        <div>
          <p class="mat-hero__eyebrow">Maternité</p>
          <h1>Suivi grossesse</h1>
          <p>Terme, visites prénatales et statut des patientes.</p>
        </div>
        <button type="button" class="btn-primary" @click="showAddModal = true">+ Nouveau dossier</button>
      </header>

      <div v-if="errorMessage" class="alert alert--error">{{ errorMessage }}</div>
      <div v-if="successMessage" class="alert alert--success">{{ successMessage }}</div>

      <div v-if="loading" class="mat-loading">Chargement…</div>

      <div v-else class="mat-table-wrap">
        <table class="mat-table">
          <thead>
            <tr>
              <th>Patiente</th>
              <th>Date terme</th>
              <th>Prochaine visite</th>
              <th>Statut</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="m in maternityList" :key="m.id" :class="{ 'row-alert': isOverdue(m.next_visit) }">
              <td class="mat-name">{{ m.nom }} {{ m.prenom }}</td>
              <td>{{ m.date_terme }}</td>
              <td>
                {{ m.next_visit }}
                <span v-if="isOverdue(m.next_visit)" class="alert-tag">Retard</span>
              </td>
              <td><span class="status-tag">{{ m.status }}</span></td>
            </tr>
            <tr v-if="!maternityList.length">
              <td colspan="4" class="empty">Aucun dossier maternité.</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="showAddModal" class="modal-overlay" @click.self="showAddModal = false">
        <div class="modal">
          <h2>Nouveau dossier maternité</h2>
          <form class="modal-form" @submit.prevent="submitForm">
            <div class="form-row">
              <div class="field">
                <label>Nom</label>
                <input v-model="form.nom" type="text" required />
              </div>
              <div class="field">
                <label>Prénom</label>
                <input v-model="form.prenom" type="text" required />
              </div>
            </div>
            <div class="form-row">
              <div class="field">
                <label>Date terme</label>
                <input v-model="form.date_terme" type="date" required />
              </div>
              <div class="field">
                <label>Prochaine visite</label>
                <input v-model="form.next_visit" type="date" required />
              </div>
            </div>
            <p v-if="formError" class="form-error">{{ formError }}</p>
            <div class="modal-actions">
              <button type="button" class="btn-ghost" @click="showAddModal = false">Annuler</button>
              <button type="submit" class="btn-primary" :disabled="saving">{{ saving ? 'Enregistrement…' : 'Enregistrer' }}</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import AppLayout from '@/components/AppLayout.vue';
import api from '@/api';

const maternityList = ref([]);
const showAddModal = ref(false);
const loading = ref(true);
const saving = ref(false);
const errorMessage = ref('');
const successMessage = ref('');
const formError = ref('');
const form = ref({ nom: '', prenom: '', date_terme: '', next_visit: '' });

const isOverdue = (date) => date && new Date(date) < new Date();

const apiError = (error, fallback) =>
  error?.response?.data?.detail || error?.response?.data?.message || fallback;

const fetchMaternityData = async () => {
  loading.value = true;
  errorMessage.value = '';
  try {
    const response = await api.instance.get('/clinical/maternity/');
    maternityList.value = Array.isArray(response.data) ? response.data : [];
  } catch (error) {
    errorMessage.value = apiError(error, 'Impossible de charger les dossiers maternité.');
    maternityList.value = [];
  } finally {
    loading.value = false;
  }
};

const submitForm = async () => {
  formError.value = '';
  if (!(form.value.nom || '').trim() || !(form.value.prenom || '').trim()) {
    formError.value = 'Nom et prénom obligatoires.';
    return;
  }
  if (form.value.next_visit && form.value.date_terme && form.value.next_visit > form.value.date_terme) {
    formError.value = 'La prochaine visite ne peut pas être après la date terme.';
    return;
  }
  saving.value = true;
  try {
    await api.instance.post('/clinical/maternity/', form.value);
    successMessage.value = 'Dossier maternité créé.';
    showAddModal.value = false;
    form.value = { nom: '', prenom: '', date_terme: '', next_visit: '' };
    await fetchMaternityData();
  } catch (error) {
    formError.value = apiError(error, 'Enregistrement impossible.');
  } finally {
    saving.value = false;
  }
};

onMounted(fetchMaternityData);
</script>

<style scoped>
.mat-page { display: flex; flex-direction: column; gap: 1.25rem; }
.mat-hero {
  display: flex; flex-wrap: wrap; justify-content: space-between; align-items: flex-end; gap: 1rem;
  padding: 1.5rem; border-radius: 16px; color: #fff;
  background: linear-gradient(135deg, #071535, #1e3a8a);
}
.mat-hero__eyebrow { font-size: 0.75rem; font-weight: 700; letter-spacing: 0.14em; text-transform: uppercase; color: #93c5fd; }
.mat-hero h1 { font-size: 1.6rem; font-weight: 800; margin-top: 0.25rem; }
.mat-hero p { font-size: 0.9rem; color: rgba(226,232,240,0.85); margin-top: 0.25rem; }
.btn-primary { padding: 0.65rem 1.1rem; border-radius: 10px; border: none; font-weight: 700; background: #2563eb; color: #fff; cursor: pointer; }
.btn-ghost { padding: 0.65rem 1.1rem; border-radius: 10px; border: 1px solid #cbd5e1; background: #fff; cursor: pointer; }
.alert { padding: 0.75rem 1rem; border-radius: 10px; font-size: 0.9rem; }
.alert--error { background: #fef2f2; color: #b91c1c; }
.alert--success { background: #eff6ff; color: #1e3a8a; }
.mat-table-wrap { background: #fff; border-radius: 14px; border: 1px solid #e2e8f0; overflow: hidden; }
.mat-table { width: 100%; border-collapse: collapse; }
.mat-table th { background: #f1f5f9; padding: 0.85rem 1rem; text-align: left; font-size: 0.8rem; text-transform: uppercase; color: #475569; }
.mat-table td { padding: 0.85rem 1rem; border-top: 1px solid #f1f5f9; }
.mat-name { font-weight: 700; color: #0b1f4a; }
.row-alert { background: #fff7ed; }
.alert-tag { margin-left: 0.4rem; font-size: 0.7rem; font-weight: 700; color: #dc2626; }
.status-tag { background: #dbeafe; color: #1e40af; padding: 0.2rem 0.5rem; border-radius: 6px; font-size: 0.75rem; font-weight: 700; }
.empty { text-align: center; color: #64748b; padding: 2rem !important; }
.mat-loading { text-align: center; padding: 2rem; color: #64748b; }
.modal-overlay { position: fixed; inset: 0; z-index: 50; display: flex; align-items: center; justify-content: center; padding: 1rem; background: rgba(7,21,53,0.55); }
.modal { width: 100%; max-width: 480px; background: #fff; border-radius: 16px; padding: 1.5rem; }
.modal h2 { font-size: 1.25rem; font-weight: 800; color: #0b1f4a; margin-bottom: 1rem; }
.modal-form { display: flex; flex-direction: column; gap: 0.85rem; }
.form-row { display: flex; gap: 0.75rem; }
.field { flex: 1; display: flex; flex-direction: column; gap: 0.35rem; }
.field label { font-size: 0.82rem; font-weight: 700; color: #0b1f4a; }
.field input { padding: 0.6rem 0.75rem; border: 1px solid #cbd5e1; border-radius: 8px; }
.form-error { color: #dc2626; font-size: 0.85rem; }
.modal-actions { display: flex; gap: 0.75rem; justify-content: flex-end; margin-top: 0.5rem; }
</style>
