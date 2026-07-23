<template>
  <AppLayout>
    <div class="ped-page">
      <header class="ped-hero">
        <div>
          <p class="ped-hero__eyebrow">Pédiatrie</p>
          <h1>Suivi pédiatrique</h1>
          <p>Nouveau-nés, vaccinations et croissance.</p>
        </div>
        <button type="button" class="btn-primary" @click="showAddModal = true">+ Nouveau dossier bébé</button>
      </header>

      <div v-if="errorMessage" class="alert alert--error">{{ errorMessage }}</div>
      <div v-if="successMessage" class="alert alert--success">{{ successMessage }}</div>

      <div v-if="loading" class="ped-loading">Chargement…</div>

      <div v-else class="ped-table-wrap">
        <table class="ped-table">
          <thead>
            <tr>
              <th>Nom du bébé</th>
              <th>Date naissance</th>
              <th>Poids</th>
              <th>Prochain vaccin</th>
              <th>Statut</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in pediatrieList" :key="p.id" :class="{ 'row-alert': isVaccineOverdue(p.vaccin_date) }">
              <td class="ped-name">{{ p.nom }}</td>
              <td>{{ p.date_naissance }}</td>
              <td>{{ p.poids }} kg</td>
              <td>
                {{ p.vaccin_date }}
                <span v-if="isVaccineOverdue(p.vaccin_date)" class="alert-tag">Retard</span>
              </td>
              <td><span class="status-tag">{{ p.status }}</span></td>
            </tr>
            <tr v-if="!pediatrieList.length">
              <td colspan="5" class="empty">Aucun dossier pédiatrique.</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="showAddModal" class="modal-overlay" @click.self="showAddModal = false">
        <div class="modal">
          <h2>Nouveau dossier pédiatrique</h2>
          <form class="modal-form" @submit.prevent="submitPediatrieForm">
            <div class="form-row">
              <div class="field">
                <label>Nom</label>
                <input v-model="newPediatrie.nom" type="text" required />
              </div>
              <div class="field">
                <label>Date naissance</label>
                <input v-model="newPediatrie.date_naissance" type="date" required />
              </div>
            </div>
            <div class="form-row">
              <div class="field">
                <label>Poids (kg)</label>
                <input v-model.number="newPediatrie.poids" type="number" step="0.1" required />
              </div>
              <div class="field">
                <label>Taille (cm)</label>
                <input v-model.number="newPediatrie.taille" type="number" />
              </div>
            </div>
            <div class="form-row">
              <div class="field">
                <label>Groupe sanguin</label>
                <input v-model="newPediatrie.groupe_sanguin" type="text" />
              </div>
              <div class="field">
                <label>Prochain vaccin</label>
                <input v-model="newPediatrie.vaccin_date" type="date" required />
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

const pediatrieList = ref([]);
const showAddModal = ref(false);
const loading = ref(true);
const saving = ref(false);
const errorMessage = ref('');
const successMessage = ref('');
const formError = ref('');
const newPediatrie = ref({
  nom: '', date_naissance: '', poids: '', taille: '', groupe_sanguin: '', vaccin_date: '',
});

const isVaccineOverdue = (date) => date && new Date(date) < new Date();

const apiError = (error, fallback) =>
  error?.response?.data?.detail || error?.response?.data?.message || fallback;

const fetchPediatrieData = async () => {
  loading.value = true;
  errorMessage.value = '';
  try {
    const response = await api.instance.get('/clinical/pediatrie/');
    pediatrieList.value = Array.isArray(response.data) ? response.data : [];
  } catch (error) {
    errorMessage.value = apiError(error, 'Impossible de charger les dossiers pédiatriques.');
    pediatrieList.value = [];
  } finally {
    loading.value = false;
  }
};

const submitPediatrieForm = async () => {
  formError.value = '';
  if ((newPediatrie.value.nom || '').trim().length < 2) {
    formError.value = 'Le nom doit contenir au moins 2 caractères.';
    return;
  }
  if (Number(newPediatrie.value.poids) <= 0) {
    formError.value = 'Le poids doit être supérieur à 0.';
    return;
  }
  saving.value = true;
  try {
    await api.instance.post('/clinical/pediatrie/', newPediatrie.value);
    successMessage.value = 'Dossier pédiatrique créé.';
    showAddModal.value = false;
    newPediatrie.value = { nom: '', date_naissance: '', poids: '', taille: '', groupe_sanguin: '', vaccin_date: '' };
    await fetchPediatrieData();
  } catch (error) {
    formError.value = apiError(error, 'Enregistrement impossible.');
  } finally {
    saving.value = false;
  }
};

onMounted(fetchPediatrieData);
</script>

<style scoped>
.ped-page { display: flex; flex-direction: column; gap: 1.25rem; }
.ped-hero {
  display: flex; flex-wrap: wrap; justify-content: space-between; align-items: flex-end; gap: 1rem;
  padding: 1.5rem; border-radius: 16px; color: #fff;
  background: linear-gradient(135deg, #071535, #1e3a8a);
}
.ped-hero__eyebrow { font-size: 0.75rem; font-weight: 700; letter-spacing: 0.14em; text-transform: uppercase; color: #93c5fd; }
.ped-hero h1 { font-size: 1.6rem; font-weight: 800; margin-top: 0.25rem; }
.ped-hero p { font-size: 0.9rem; color: rgba(226,232,240,0.85); margin-top: 0.25rem; }
.btn-primary {
  padding: 0.65rem 1.1rem; border-radius: 10px; border: none; font-weight: 700;
  background: #2563eb; color: #fff; cursor: pointer;
}
.btn-ghost { padding: 0.65rem 1.1rem; border-radius: 10px; border: 1px solid #cbd5e1; background: #fff; cursor: pointer; }
.alert { padding: 0.75rem 1rem; border-radius: 10px; font-size: 0.9rem; }
.alert--error { background: #fef2f2; color: #b91c1c; }
.alert--success { background: #eff6ff; color: #1e3a8a; }
.ped-table-wrap { background: #fff; border-radius: 14px; border: 1px solid #e2e8f0; overflow: hidden; }
.ped-table { width: 100%; border-collapse: collapse; }
.ped-table th { background: #f1f5f9; padding: 0.85rem 1rem; text-align: left; font-size: 0.8rem; text-transform: uppercase; color: #475569; }
.ped-table td { padding: 0.85rem 1rem; border-top: 1px solid #f1f5f9; }
.ped-name { font-weight: 700; color: #0b1f4a; }
.row-alert { background: #fff7ed; }
.alert-tag { margin-left: 0.4rem; font-size: 0.7rem; font-weight: 700; color: #dc2626; }
.status-tag { background: #dbeafe; color: #1e40af; padding: 0.2rem 0.5rem; border-radius: 6px; font-size: 0.75rem; font-weight: 700; }
.empty { text-align: center; color: #64748b; padding: 2rem !important; }
.ped-loading { text-align: center; padding: 2rem; color: #64748b; }
.modal-overlay {
  position: fixed; inset: 0; z-index: 50; display: flex; align-items: center; justify-content: center;
  padding: 1rem; background: rgba(7,21,53,0.55);
}
.modal { width: 100%; max-width: 520px; background: #fff; border-radius: 16px; padding: 1.5rem; }
.modal h2 { font-size: 1.25rem; font-weight: 800; color: #0b1f4a; margin-bottom: 1rem; }
.modal-form { display: flex; flex-direction: column; gap: 0.85rem; }
.form-row { display: flex; gap: 0.75rem; }
.field { flex: 1; display: flex; flex-direction: column; gap: 0.35rem; }
.field label { font-size: 0.82rem; font-weight: 700; color: #0b1f4a; }
.field input { padding: 0.6rem 0.75rem; border: 1px solid #cbd5e1; border-radius: 8px; }
.form-error { color: #dc2626; font-size: 0.85rem; }
.modal-actions { display: flex; gap: 0.75rem; justify-content: flex-end; margin-top: 0.5rem; }
</style>
