<template>
  <div class="consultation-container">
    <h2>🩺 Nouvelle Consultation Médicale</h2>
    
    <form @submit.prevent="submitConsultation" class="consultation-form">
      <div class="form-group">
        <label for="patient">Sélectionner le Patient :</label>
        <select id="patient" v-model="form.patient_id" required>
          <option value="" disabled>-- Choisissez un patient --</option>
          <option v-for="patient in patients" :key="patient.id" :value="patient.id">
            {{ patient.nom }} {{ patient.prenom }} ({{ patient.matricule }})
          </option>
        </select>
      </div>

      <div class="form-group">
        <label for="symptoms">Symptômes constatés :</label>
        <textarea id="symptoms" v-model="form.symptoms" rows="3" placeholder="Ex: Fièvre persistante, maux de tête..." required></textarea>
      </div>

      <div class="form-group">
        <label for="diagnosis">Diagnostic médical :</label>
        <textarea id="diagnosis" v-model="form.diagnosis" rows="3" placeholder="Ex: Paludisme suspecté, Grippe saisonnière..." required></textarea>
      </div>

      <div class="form-group">
        <label for="prescription">Prescription / Ordonnance (Optionnel) :</label>
        <textarea id="prescription" v-model="form.prescription" rows="3" placeholder="Ex: Paracétamol 500mg..."></textarea>
      </div>

      <div class="form-group checkbox-group">
        <input type="checkbox" id="hospitalization" v-model="form.requires_hospitalization" @change="fetchAvailableBeds" />
        <label for="hospitalization">⚠️ Recommandation d'hospitalisation immédiate</label>
      </div>

      <div v-if="form.requires_hospitalization" class="form-group fade-in">
        <label for="bed">Attribuer un Lit disponible :</label>
        <select id="bed" v-model="form.bed_id" :required="form.requires_hospitalization">
          <option value="" disabled>-- Choisissez un lit disponible --</option>
          <option v-for="bed in availableBeds" :key="bed.id" :value="bed.id">
            Lit N°{{ bed.number }} - Salle {{ bed.room_number }} ({{ bed.service_name }})
          </option>
        </select>
      </div>

      <button type="submit" class="btn-submit" :disabled="loading">
        {{ loading ? 'Enregistrement en cours...' : '💾 Enregistrer la Consultation' }}
      </button>
    </form>

    <p v-if="errorMessage" class="alert-error">❌ {{ errorMessage }}</p>
    <p v-if="successMessage" class="alert-success">✅ {{ successMessage }}</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import api from '@/api'; // Correction du chemin

const patients = ref([]);
const availableBeds = ref([]);
const loading = ref(false);
const errorMessage = ref('');
const successMessage = ref('');

const form = ref({
  patient_id: '',
  symptoms: '',
  diagnosis: '',
  prescription: '',
  requires_hospitalization: false,
  bed_id: null
});

const fetchPatients = async () => {
  try {
    const response = await api.instance.get('/clinical/patients/');
    patients.value = response.data;
  } catch (error) {
    errorMessage.value = "Impossible de récupérer la liste des patients.";
  }
};

const fetchAvailableBeds = async () => {
  if (!form.value.requires_hospitalization) {
    form.value.bed_id = null;
    return;
  }
  try {
    const response = await api.instance.get('/clinical/beds/available/');
    availableBeds.value = response.data;
  } catch (error) {
    errorMessage.value = "Impossible de charger la liste des lits disponibles.";
  }
};

const submitConsultation = async () => {
  loading.value = true;
  errorMessage.value = '';
  successMessage.value = '';

  try {
    await api.instance.post('/clinical/consultations/', form.value);
    successMessage.value = "La consultation a été enregistrée avec succès !";
    form.value = { patient_id: '', symptoms: '', diagnosis: '', prescription: '', requires_hospitalization: false, bed_id: null };
  } catch (error) {
    errorMessage.value = error.response?.data?.detail || "Une erreur est survenue.";
  } finally {
    loading.value = false;
  }
};

onMounted(() => { fetchPatients(); });
</script>

<style scoped>
/* Tes styles restent identiques, ils sont très bien */
.consultation-container { max-width: 650px; margin: 30px auto; padding: 25px; background: #ffffff; border-radius: 12px; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1); }
h2 { color: #2c3e50; text-align: center; margin-bottom: 25px; }
.consultation-form { display: flex; flex-direction: column; gap: 18px; }
.form-group { display: flex; flex-direction: column; gap: 6px; }
label { font-weight: 600; color: #34495e; }
select, textarea { padding: 10px; border: 1px solid #ccd1d9; border-radius: 6px; }
.checkbox-group { flex-direction: row; align-items: center; gap: 10px; background: #f8f9fa; padding: 12px; border-radius: 6px; }
.btn-submit { background: #2ecc71; color: white; padding: 12px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; }
.alert-error { color: #e74c3c; font-weight: bold; text-align: center; }
.alert-success { color: #2ecc71; font-weight: bold; text-align: center; }
</style>