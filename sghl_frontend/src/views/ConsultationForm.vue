<template>
  <div class="consultation-container">
    <h2>Nouvelle consultation médicale</h2>

    <form @submit.prevent="submitConsultation" class="consultation-form">
      <div class="form-group">
        <label for="patient">Patient</label>
        <select id="patient" v-model.number="form.patient_id" required>
          <option :value="0" disabled>-- Choisissez un patient --</option>
          <option v-for="patient in patients" :key="patient.id" :value="patient.id">
            {{ patient.nom }} {{ patient.prenom }} ({{ patient.matricule }})
          </option>
        </select>
      </div>

      <div class="form-group">
        <label for="symptoms">Symptômes constatés</label>
        <textarea
          id="symptoms"
          v-model="form.symptoms"
          rows="3"
          minlength="3"
          placeholder="Ex: Fièvre persistante, maux de tête..."
          required
        />
      </div>

      <div class="form-group">
        <label for="diagnosis">Diagnostic médical</label>
        <textarea
          id="diagnosis"
          v-model="form.diagnosis"
          rows="3"
          minlength="3"
          placeholder="Ex: Paludisme suspecté..."
          required
        />
      </div>

      <div class="form-group">
        <label for="prescription">Prescription / Ordonnance (optionnel)</label>
        <textarea
          id="prescription"
          v-model="form.prescription"
          rows="3"
          placeholder="Ex: Paracétamol 500mg..."
        />
      </div>

      <div class="form-group checkbox-group">
        <input
          type="checkbox"
          id="hospitalization"
          v-model="form.requires_hospitalization"
          @change="onHospitalizationToggle"
        />
        <label for="hospitalization">Hospitalisation immédiate</label>
      </div>

      <div v-if="form.requires_hospitalization" class="form-group">
        <label for="bed">Lit disponible</label>
        <select id="bed" v-model.number="form.bed_id" :required="form.requires_hospitalization">
          <option :value="0" disabled>-- Choisissez un lit --</option>
          <option v-for="bed in availableBeds" :key="bed.id" :value="bed.id">
            Lit {{ bed.number }} — Chambre {{ bed.room_number }} ({{ bed.service_name }})
          </option>
        </select>
        <p v-if="!availableBeds.length" class="hint">Aucun lit libre. Vérifiez le module Admission.</p>
      </div>

      <button type="submit" class="btn-submit" :disabled="loading">
        {{ loading ? 'Enregistrement...' : 'Enregistrer la consultation' }}
      </button>
    </form>

    <p v-if="errorMessage" class="alert-error">{{ errorMessage }}</p>
    <p v-if="successMessage" class="alert-success">{{ successMessage }}</p>

    <div v-if="lastResult?.id" class="receipt-box">
      <p>
        Facture #{{ lastResult.invoice_id }} —
        {{ Number(lastResult.invoice_amount || 0).toLocaleString('fr-FR') }} FCFA
      </p>
      <button type="button" class="btn-receipt" @click="downloadReceipt(lastResult.id)">
        Télécharger le reçu PDF
      </button>
    </div>

    <section v-if="recent.length" class="recent">
      <h3>Dernières consultations</h3>
      <ul>
        <li v-for="c in recent" :key="c.id">
          <strong>{{ c.patient_name }}</strong> — {{ c.diagnosis }}
          <span class="meta">{{ formatDate(c.date) }} · Dr {{ c.doctor_username }}</span>
        </li>
      </ul>
    </section>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue';
import api from '@/api';
import { getApiBaseUrl } from '@/apiBase';

const patients = ref([]);
const availableBeds = ref([]);
const recent = ref([]);
const lastResult = ref(null);
const loading = ref(false);
const errorMessage = ref('');
const successMessage = ref('');

const form = reactive({
  patient_id: 0,
  symptoms: '',
  diagnosis: '',
  prescription: '',
  requires_hospitalization: false,
  bed_id: 0,
});

const apiBase = getApiBaseUrl();

const apiError = (error, fallback) =>
  error?.response?.data?.detail || error?.response?.data?.message || fallback;

const downloadReceipt = async (consultationId) => {
  const response = await fetch(`${apiBase}/clinical/consultations/${consultationId}/receipt/pdf`, {
    headers: { Authorization: `Bearer ${localStorage.getItem('token') || ''}` },
  });
  if (!response.ok) throw new Error('Reçu indisponible');
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `recu_consultation_${consultationId}.pdf`;
  a.click();
  URL.revokeObjectURL(url);
};

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

const fetchRecent = async () => {
  try {
    const response = await api.instance.get('/clinical/consultations/recent');
    recent.value = Array.isArray(response.data) ? response.data : [];
  } catch {
    recent.value = [];
  }
};

const fetchAvailableBeds = async () => {
  const response = await api.instance.get('/clinical/beds/available');
  availableBeds.value = Array.isArray(response.data) ? response.data : [];
};

const onHospitalizationToggle = async () => {
  form.bed_id = 0;
  if (form.requires_hospitalization) {
    try {
      await fetchAvailableBeds();
    } catch (error) {
      errorMessage.value = apiError(error, 'Impossible de charger les lits disponibles.');
    }
  }
};

const resetForm = () => {
  form.patient_id = 0;
  form.symptoms = '';
  form.diagnosis = '';
  form.prescription = '';
  form.requires_hospitalization = false;
  form.bed_id = 0;
};

const submitConsultation = async () => {
  loading.value = true;
  errorMessage.value = '';
  successMessage.value = '';

  if (!form.patient_id) {
    errorMessage.value = 'Sélectionnez un patient.';
    loading.value = false;
    return;
  }
  if (form.symptoms.trim().length < 3 || form.diagnosis.trim().length < 3) {
    errorMessage.value = 'Symptômes et diagnostic : minimum 3 caractères.';
    loading.value = false;
    return;
  }
  if (form.requires_hospitalization && !form.bed_id) {
    errorMessage.value = 'Sélectionnez un lit pour l’hospitalisation.';
    loading.value = false;
    return;
  }

  try {
    const payload = {
      patient_id: form.patient_id,
      symptoms: form.symptoms.trim(),
      diagnosis: form.diagnosis.trim(),
      prescription: form.prescription.trim() || null,
      requires_hospitalization: form.requires_hospitalization,
      bed_id: form.requires_hospitalization ? form.bed_id : null,
    };
    const response = await api.instance.post('/clinical/consultations', payload);
    lastResult.value = response.data;
    successMessage.value = form.requires_hospitalization
      ? 'Consultation enregistrée et patient hospitalisé. Facture/reçu générés.'
      : 'Consultation enregistrée. Facture/reçu générés.';
    resetForm();
    await fetchRecent();
  } catch (error) {
    errorMessage.value = apiError(error, 'Une erreur est survenue.');
  } finally {
    loading.value = false;
  }
};

onMounted(async () => {
  try {
    await Promise.all([fetchPatients(), fetchRecent()]);
  } catch (error) {
    errorMessage.value = apiError(error, 'Impossible de charger les données.');
  }
});
</script>

<style scoped>
.consultation-container {
  max-width: 720px;
  margin: 0 auto;
  padding: 24px;
  background: #fff;
  border-radius: 16px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 4px 16px rgba(15, 23, 42, 0.06);
}
h2 { color: #0f172a; text-align: center; margin: 0 0 22px; font-size: 1.4rem; }
h3 { margin: 0 0 12px; font-size: 1rem; color: #334155; }
.consultation-form { display: flex; flex-direction: column; gap: 16px; }
.form-group { display: flex; flex-direction: column; gap: 6px; }
label { font-weight: 600; color: #334155; font-size: 0.9rem; }
select, textarea {
  padding: 10px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font: inherit;
}
.checkbox-group {
  flex-direction: row;
  align-items: center;
  gap: 10px;
  background: #f8fafc;
  padding: 12px;
  border-radius: 8px;
}
.btn-submit {
  background: #059669;
  color: #fff;
  padding: 12px;
  border: none;
  border-radius: 8px;
  font-weight: 700;
  cursor: pointer;
}
.btn-submit:disabled { opacity: 0.6; cursor: not-allowed; }
.alert-error { color: #dc2626; font-weight: 600; text-align: center; margin-top: 14px; }
.alert-success { color: #059669; font-weight: 600; text-align: center; margin-top: 14px; }
.receipt-box {
  margin-top: 16px;
  padding: 14px;
  border-radius: 10px;
  background: #ecfdf5;
  border: 1px solid #a7f3d0;
  text-align: center;
}
.btn-receipt {
  margin-top: 10px;
  background: #0f766e;
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 10px 14px;
  font-weight: 700;
  cursor: pointer;
}
.hint { font-size: 0.8rem; color: #64748b; }
.recent { margin-top: 28px; border-top: 1px solid #e2e8f0; padding-top: 18px; }
.recent ul { list-style: none; padding: 0; margin: 0; display: grid; gap: 10px; }
.recent li { background: #f8fafc; border-radius: 8px; padding: 10px 12px; }
.meta { display: block; font-size: 0.8rem; color: #64748b; margin-top: 4px; }
</style>
