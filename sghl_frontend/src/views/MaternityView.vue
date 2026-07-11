<template>
  <AppLayout>
    <div class="dashboard-container">
      <div class="sidebar">
        <div class="sidebar-brand">
          <h2>SGHL 🏥</h2>
          <span class="user-role">Service Maternité</span>
        </div>
        <nav class="sidebar-menu">
          <button @click="$router.push('/dashboard')">← Retour Dashboard</button>
        </nav>
      </div>

      <div class="main-content">
        <header class="content-header">
          <div>
            <h1>🤰 Suivi Maternité & Pédiatrie</h1>
            <p>Suivi de grossesse et évolution fœtale.</p>
          </div>
          <button class="btn-add-patient" @click="showAddModal = true">＋ Nouveau Dossier</button>
        </header>

        <div class="pregnancy-visuals">
          <p class="section-title">Évolution de la grossesse :</p>

        </div>

        <div class="table-container">
          <table class="patients-table">
            <thead>
              <tr>
                <th>Patiente</th>
                <th>Date Terme</th>
                <th>Prochaine Visite</th>
                <th>Statut</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="m in maternityList" :key="m.id" :class="{ 'row-alert': isOverdue(m.next_visit) }">
                <td class="patient-name">{{ m.nom }} {{ m.prenom }}</td>
                <td>{{ m.date_terme }}</td>
                <td>
                  {{ m.next_visit }}
                  <span v-if="isOverdue(m.next_visit)" class="alert-text">⚠️ Retard</span>
                </td>
                <td><span class="status-tag active">{{ m.status }}</span></td>
                <td><button class="btn-action edit">👁️ Suivi</button></td>
              </tr>
            </tbody>
          </table>
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

// Vérifie si la date est dépassée
const isOverdue = (date) => {
  if (!date) return false;
  return new Date(date) < new Date();
};

const fetchMaternityData = async () => {
  try {
    const response = await api.instance.get('/clinical/maternity/');
    maternityList.value = response.data;
  } catch (error) { console.error("Erreur chargement", error); }
};

onMounted(fetchMaternityData);
</script>

<style scoped>
/* Styles ajoutés pour l'alerte et les visuels */
.pregnancy-visuals { margin-bottom: 20px; background: white; padding: 20px; border-radius: 8px; text-align: center; }
.section-title { font-weight: bold; margin-bottom: 15px; color: #34495e; }
.row-alert { background-color: #fff1f0 !important; border-left: 4px solid #e74c3c; }
.alert-text { color: #e74c3c; font-size: 0.7rem; font-weight: bold; margin-left: 5px; }
/* ... (Garder le reste de tes styles existants) ... */
</style>