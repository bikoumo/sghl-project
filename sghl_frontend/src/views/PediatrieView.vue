<template>
  <AppLayout>
    <div class="dashboard-container">
      <div class="sidebar">
        <div class="sidebar-brand">
          <h2>SGHL 🏥</h2>
          <span class="user-role">Service Pédiatrie</span>
        </div>
        <nav class="sidebar-menu">
          <button @click="$router.push('/dashboard')">← Retour Dashboard</button>
          <button @click="$router.push('/maternity')">🤰 Maternité</button>
        </nav>
      </div>

      <div class="main-content">
        <header class="content-header">
          <div>
            <h1>👶 Suivi Pédiatrique</h1>
            <p>Gestion des nouveau-nés, vaccinations et croissance.</p>
          </div>
          <button class="btn-add-patient" @click="showAddModal = true">＋ Nouveau Dossier Bébé</button>
        </header>

        <div class="visual-section">
          <p class="section-title">Croissance et développement :</p>
          <div class="placeholder-img"><em>[Images : Courbes de croissance / Étapes développement]</em></div>
        </div>

        <div class="table-container">
          <table class="patients-table">
            <thead>
              <tr>
                <th>Nom du Bébé</th>
                <th>Date Naissance</th>
                <th>Poids (kg)</th>
                <th>Prochain Vaccin</th>
                <th>Statut</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="p in pediatrieList" :key="p.id" :class="{ 'row-alert': isVaccineOverdue(p.vaccin_date) }">
                <td class="patient-name">{{ p.nom }}</td>
                <td>{{ p.date_naissance }}</td>
                <td>{{ p.poids }} kg</td>
                <td>
                  {{ p.vaccin_date }}
                  <span v-if="isVaccineOverdue(p.vaccin_date)" class="alert-text">⚠️ Retard</span>
                </td>
                <td><span class="status-tag">{{ p.status }}</span></td>
                <td><button class="btn-action edit">👁️ Carnet</button></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div v-if="showAddModal" class="modal-overlay">
        <div class="modal-content">
          <div class="modal-header">
            <h2>👶 Nouveau Dossier Pédiatrique</h2>
            <button @click="showAddModal = false" class="btn-close">&times;</button>
          </div>
          <form @submit.prevent="submitPediatrieForm" class="patient-form">
            <div class="form-row">
              <div class="form-group"><label>Nom :</label><input type="text" v-model="newPediatrie.nom" required /></div>
              <div class="form-group"><label>Date Naissance :</label><input type="date" v-model="newPediatrie.date_naissance" required /></div>
            </div>
            <div class="form-row">
              <div class="form-group"><label>Poids (kg) :</label><input type="number" step="0.1" v-model="newPediatrie.poids" required /></div>
              <div class="form-group"><label>Taille (cm) :</label><input type="number" v-model="newPediatrie.taille" /></div>
            </div>
            <div class="form-row">
              <div class="form-group"><label>Groupe Sanguin :</label><input type="text" v-model="newPediatrie.groupe_sanguin" /></div>
              <div class="form-group"><label>Date prochain Vaccin :</label><input type="date" v-model="newPediatrie.vaccin_date" required /></div>
            </div>
            <div class="modal-actions">
              <button type="button" @click="showAddModal = false" class="btn-cancel">Annuler</button>
              <button type="submit" class="btn-submit">Enregistrer</button>
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
const newPediatrie = ref({ nom: '', date_naissance: '', poids: '', taille: '', groupe_sanguin: '', vaccin_date: '' });

const isVaccineOverdue = (date) => new Date(date) < new Date();

const fetchPediatrieData = async () => {
  try {
    const response = await api.instance.get('/clinical/pediatrie/');
    pediatrieList.value = response.data;
  } catch (error) { console.error("Erreur chargement pédiatrie", error); }
};

const submitPediatrieForm = async () => {
  try {
    await api.instance.post('/clinical/pediatrie/', newPediatrie.value);
    alert('Dossier pédiatrique créé !');
    showAddModal.value = false;
    fetchPediatrieData();
  } catch (error) { console.error("Erreur enregistrement", error); }
};

onMounted(fetchPediatrieData);
</script>

<style scoped>
.dashboard-container { display: flex; min-height: 100vh; background-color: #f5f7fa; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
.sidebar { width: 260px; background-color: #2c3e50; color: white; padding: 25px 20px; }
.main-content { flex: 1; padding: 40px; }
.content-header { display: flex; justify-content: space-between; margin-bottom: 25px; }
.visual-section { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; text-align: center; border: 1px dashed #cbd5e0; }
.placeholder-img { padding: 40px; color: #a0aec0; }
.table-container { background: white; border-radius: 8px; overflow: hidden; }
.patients-table { width: 100%; border-collapse: collapse; }
.patients-table th { background-color: #f8f9fa; padding: 15px; text-align: left; }
.patients-table td { padding: 15px; border-bottom: 1px solid #edf2f7; }
.btn-add-patient { background-color: #3498db; color: white; border: none; padding: 12px 20px; border-radius: 6px; cursor: pointer; }
.row-alert { background-color: #fff1f0 !important; }
.alert-text { color: #e74c3c; font-size: 0.7rem; font-weight: bold; margin-left: 5px; }
/* Modal Styles (identiques) */
.modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); display: flex; justify-content: center; align-items: center; z-index: 1000; }
.modal-content { background: white; padding: 30px; border-radius: 8px; width: 100%; max-width: 600px; }
.patient-form { display: flex; flex-direction: column; gap: 15px; }
.form-row { display: flex; gap: 15px; }
.form-group { display: flex; flex-direction: column; gap: 5px; flex: 1; }
.modal-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 15px; }
.btn-submit { background-color: #2ecc71; color: white; padding: 10px 20px; border-radius: 6px; border: none; cursor: pointer; }
.btn-cancel { background-color: #95a5a6; color: white; padding: 10px 20px; border-radius: 6px; border: none; cursor: pointer; }
</style>