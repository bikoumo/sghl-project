<template>
  <AppLayout>
    <div class="lab-page">
      <header class="lab-hero">
        <div>
          <p class="lab-hero__eyebrow">Laboratoire</p>
          <h1>Examens &amp; résultats</h1>
          <p>Demandes d'analyses biologiques et saisie des résultats.</p>
        </div>
        <button type="button" class="btn-primary" @click="showAddModal = true">+ Nouvelle demande</button>
      </header>

      <div v-if="errorMessage" class="alert alert--error">{{ errorMessage }}</div>
      <div v-if="successMessage" class="alert alert--success">{{ successMessage }}</div>
      <div v-if="loading" class="lab-loading">Chargement…</div>

      <div v-else class="lab-table-wrap">
        <table class="lab-table">
          <thead>
            <tr>
              <th>Patient</th>
              <th>Examen</th>
              <th>Statut</th>
              <th>Demandé le</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="exam in exams" :key="exam.id">
              <td class="lab-name">{{ exam.patient_name }}</td>
              <td>
                <strong>{{ exam.title }}</strong>
                <p v-if="exam.description" class="lab-desc">{{ exam.description }}</p>
              </td>
              <td><span class="status-tag" :class="`status-tag--${exam.status.toLowerCase()}`">{{ statusLabel(exam.status) }}</span></td>
              <td>{{ formatDate(exam.requested_at) }}</td>
              <td>
                <button
                  v-if="exam.status !== 'COMPLETED'"
                  type="button"
                  class="btn-sm"
                  @click="openResultModal(exam)"
                >
                  Saisir résultat
                </button>
                <span v-else class="lab-result">{{ exam.conclusion || exam.result_text }}</span>
              </td>
            </tr>
            <tr v-if="!exams.length">
              <td colspan="5" class="empty">Aucune demande d'examen.</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Modal nouvelle demande -->
      <div v-if="showAddModal" class="modal-overlay" @click.self="showAddModal = false">
        <div class="modal">
          <h2>Nouvelle demande d'examen</h2>
          <form class="modal-form" @submit.prevent="submitExam">
            <div class="field">
              <label>Patient</label>
              <select v-model.number="form.patient_id" required>
                <option value="" disabled>— Choisir —</option>
                <option v-for="p in patients" :key="p.id" :value="p.id">{{ p.nom }} {{ p.prenom }}</option>
              </select>
            </div>
            <div class="field">
              <label>Titre de l'examen</label>
              <input v-model="form.title" type="text" required minlength="2" />
            </div>
            <div class="field">
              <label>Description (optionnel)</label>
              <textarea v-model="form.description" rows="3" />
            </div>
            <p v-if="formError" class="form-error">{{ formError }}</p>
            <div class="modal-actions">
              <button type="button" class="btn-ghost" @click="showAddModal = false">Annuler</button>
              <button type="submit" class="btn-primary" :disabled="saving">{{ saving ? 'Enregistrement…' : 'Créer' }}</button>
            </div>
          </form>
        </div>
      </div>

      <!-- Modal résultat -->
      <div v-if="resultModal" class="modal-overlay" @click.self="resultModal = null">
        <div class="modal">
          <h2>Résultat — {{ resultModal.title }}</h2>
          <form class="modal-form" @submit.prevent="submitResult">
            <div class="field">
              <label>Résultats</label>
              <textarea v-model="resultForm.result_text" rows="4" required minlength="2" />
            </div>
            <div class="field">
              <label>Conclusion</label>
              <textarea v-model="resultForm.conclusion" rows="2" />
            </div>
            <p v-if="formError" class="form-error">{{ formError }}</p>
            <div class="modal-actions">
              <button type="button" class="btn-ghost" @click="resultModal = null">Annuler</button>
              <button type="submit" class="btn-primary" :disabled="saving">{{ saving ? 'Enregistrement…' : 'Valider' }}</button>
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

const exams = ref([]);
const patients = ref([]);
const loading = ref(true);
const saving = ref(false);
const showAddModal = ref(false);
const resultModal = ref(null);
const errorMessage = ref('');
const successMessage = ref('');
const formError = ref('');
const form = ref({ patient_id: '', title: '', description: '' });
const resultForm = ref({ result_text: '', conclusion: '' });

const apiError = (error, fallback) =>
  error?.response?.data?.detail || error?.response?.data?.message || fallback;

const statusLabel = (s) => ({ PENDING: 'En attente', IN_PROGRESS: 'En cours', COMPLETED: 'Terminé' }[s] || s);
const formatDate = (d) => {
  try { return new Date(d).toLocaleString('fr-FR'); } catch { return d; }
};

const fetchAll = async () => {
  loading.value = true;
  errorMessage.value = '';
  try {
    const [examsRes, patientsRes] = await Promise.all([
      api.instance.get('/clinical/exams/'),
      api.getPatients(),
    ]);
    exams.value = Array.isArray(examsRes.data) ? examsRes.data : [];
    const pdata = patientsRes.data;
    patients.value = Array.isArray(pdata) ? pdata : (pdata?.patients || []);
  } catch (error) {
    errorMessage.value = apiError(error, 'Impossible de charger le laboratoire.');
  } finally {
    loading.value = false;
  }
};

const submitExam = async () => {
  formError.value = '';
  if ((form.value.title || '').trim().length < 2) {
    formError.value = 'Titre obligatoire (min. 2 caractères).';
    return;
  }
  saving.value = true;
  try {
    await api.instance.post('/clinical/exams/', form.value);
    successMessage.value = 'Demande créée.';
    showAddModal.value = false;
    form.value = { patient_id: '', title: '', description: '' };
    await fetchAll();
  } catch (error) {
    formError.value = apiError(error, 'Création impossible.');
  } finally {
    saving.value = false;
  }
};

const openResultModal = (exam) => {
  resultModal.value = exam;
  resultForm.value = { result_text: '', conclusion: '' };
  formError.value = '';
};

const submitResult = async () => {
  formError.value = '';
  if ((resultForm.value.result_text || '').trim().length < 2) {
    formError.value = 'Résultat obligatoire (min. 2 caractères).';
    return;
  }
  saving.value = true;
  try {
    await api.instance.post(`/clinical/exams/${resultModal.value.id}/result`, resultForm.value);
    successMessage.value = 'Résultat enregistré.';
    resultModal.value = null;
    await fetchAll();
  } catch (error) {
    formError.value = apiError(error, 'Enregistrement impossible.');
  } finally {
    saving.value = false;
  }
};

onMounted(fetchAll);
</script>

<style scoped>
.lab-page { display: flex; flex-direction: column; gap: 1.25rem; }
.lab-hero {
  display: flex; flex-wrap: wrap; justify-content: space-between; align-items: flex-end; gap: 1rem;
  padding: 1.5rem; border-radius: 16px; color: #fff;
  background: linear-gradient(135deg, #071535, #1e3a8a);
}
.lab-hero__eyebrow { font-size: 0.75rem; font-weight: 700; letter-spacing: 0.14em; text-transform: uppercase; color: #93c5fd; }
.lab-hero h1 { font-size: 1.6rem; font-weight: 800; margin-top: 0.25rem; }
.lab-hero p { font-size: 0.9rem; color: rgba(226,232,240,0.85); margin-top: 0.25rem; }
.btn-primary { padding: 0.65rem 1.1rem; border-radius: 10px; border: none; font-weight: 700; background: #2563eb; color: #fff; cursor: pointer; }
.btn-ghost { padding: 0.65rem 1.1rem; border-radius: 10px; border: 1px solid #cbd5e1; background: #fff; cursor: pointer; }
.btn-sm { padding: 0.35rem 0.7rem; border-radius: 8px; border: none; background: #1e3a8a; color: #fff; font-size: 0.8rem; font-weight: 600; cursor: pointer; }
.alert { padding: 0.75rem 1rem; border-radius: 10px; font-size: 0.9rem; }
.alert--error { background: #fef2f2; color: #b91c1c; }
.alert--success { background: #eff6ff; color: #1e3a8a; }
.lab-table-wrap { background: #fff; border-radius: 14px; border: 1px solid #e2e8f0; overflow: hidden; }
.lab-table { width: 100%; border-collapse: collapse; }
.lab-table th { background: #f1f5f9; padding: 0.85rem 1rem; text-align: left; font-size: 0.8rem; text-transform: uppercase; color: #475569; }
.lab-table td { padding: 0.85rem 1rem; border-top: 1px solid #f1f5f9; vertical-align: top; }
.lab-name { font-weight: 700; color: #0b1f4a; }
.lab-desc { font-size: 0.8rem; color: #64748b; margin-top: 0.2rem; }
.lab-result { font-size: 0.85rem; color: #047857; }
.status-tag { padding: 0.2rem 0.5rem; border-radius: 6px; font-size: 0.75rem; font-weight: 700; }
.status-tag--pending { background: #fef3c7; color: #92400e; }
.status-tag--in_progress { background: #dbeafe; color: #1e40af; }
.status-tag--completed { background: #d1fae5; color: #047857; }
.empty { text-align: center; color: #64748b; padding: 2rem !important; }
.lab-loading { text-align: center; padding: 2rem; color: #64748b; }
.modal-overlay { position: fixed; inset: 0; z-index: 50; display: flex; align-items: center; justify-content: center; padding: 1rem; background: rgba(7,21,53,0.55); }
.modal { width: 100%; max-width: 520px; background: #fff; border-radius: 16px; padding: 1.5rem; }
.modal h2 { font-size: 1.25rem; font-weight: 800; color: #0b1f4a; margin-bottom: 1rem; }
.modal-form { display: flex; flex-direction: column; gap: 0.85rem; }
.field { display: flex; flex-direction: column; gap: 0.35rem; }
.field label { font-size: 0.82rem; font-weight: 700; color: #0b1f4a; }
.field input, .field select, .field textarea { padding: 0.6rem 0.75rem; border: 1px solid #cbd5e1; border-radius: 8px; }
.form-error { color: #dc2626; font-size: 0.85rem; }
.modal-actions { display: flex; gap: 0.75rem; justify-content: flex-end; margin-top: 0.5rem; }
</style>
