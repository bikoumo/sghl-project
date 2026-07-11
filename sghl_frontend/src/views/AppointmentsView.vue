<template>
  <AppLayout>
    <div class="p-6 space-y-6">
      <!-- Header -->
      <header class="flex justify-between items-center">
        <div>
          <h1 class="text-3xl font-bold text-slate-900">📅 Gestion des Rendez-vous</h1>
          <p class="text-slate-600 mt-1">Planification et gestion des consultations médicales</p>
        </div>
        <button @click="showAddModal = true" class="bg-emerald-600 hover:bg-emerald-700 text-white px-6 py-3 rounded-lg font-semibold transition shadow-sm">
          ＋ Nouveau Rendez-vous
        </button>
      </header>

      <!-- Info Banner -->
      <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 flex items-center gap-4">
        <span class="text-2xl flex-shrink-0">ℹ️</span>
        <div>
          <p class="text-blue-900 font-medium">Validations Métier</p>
          <p class="text-blue-800 text-sm">
            • Les rendez-vous ne peuvent être pris moins de 2 heures avant
            • Maximum 10 rendez-vous par jour
            • Les erreurs seront affichées ci-dessous
          </p>
        </div>
      </div>

      <!-- Error Alert -->
      <div v-if="errorMessage" class="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center gap-4">
        <span class="text-2xl flex-shrink-0">❌</span>
        <div class="flex-1">
          <p class="text-red-900 font-medium">Erreur d'enregistrement</p>
          <p class="text-red-800 text-sm whitespace-pre-wrap">{{ errorMessage }}</p>
        </div>
        <button @click="errorMessage = ''" class="text-red-600 hover:text-red-800">
          <span class="text-xl">✕</span>
        </button>
      </div>

      <!-- Success Alert -->
      <div v-if="successMessage" class="bg-emerald-50 border border-emerald-200 rounded-lg p-4 flex items-center gap-4">
        <span class="text-2xl flex-shrink-0">✅</span>
        <div class="flex-1">
          <p class="text-emerald-900 font-medium">Succès</p>
          <p class="text-emerald-800 text-sm">{{ successMessage }}</p>
        </div>
        <button @click="successMessage = ''" class="text-emerald-600 hover:text-emerald-800">
          <span class="text-xl">✕</span>
        </button>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="bg-white rounded-xl border border-slate-200 p-8 text-center">
        <p class="text-slate-600">⏳ Chargement des rendez-vous...</p>
      </div>

      <!-- Appointments Table -->
      <div v-else class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <table class="w-full text-left">
          <thead>
            <tr class="bg-slate-50 border-b border-slate-200">
              <th class="px-6 py-4 text-xs font-semibold text-slate-700 uppercase">Patient</th>
              <th class="px-6 py-4 text-xs font-semibold text-slate-700 uppercase">Médecin</th>
              <th class="px-6 py-4 text-xs font-semibold text-slate-700 uppercase">Date & Heure</th>
              <th class="px-6 py-4 text-xs font-semibold text-slate-700 uppercase">Service</th>
              <th class="px-6 py-4 text-xs font-semibold text-slate-700 uppercase">Statut</th>
              <th class="px-6 py-4 text-xs font-semibold text-slate-700 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="appt in appointments" :key="appt.id" class="border-b border-slate-100 hover:bg-slate-50 transition">
              <td class="px-6 py-4 font-medium text-slate-900">{{ appt.patient__username }}</td>
              <td class="px-6 py-4 text-slate-700">{{ appt.doctor__username }}</td>
              <td class="px-6 py-4 text-slate-700">
                {{ formatDateTime(appt.appointment_date) }}
              </td>
              <td class="px-6 py-4 text-slate-700">{{ appt.service__name || 'N/A' }}</td>
              <td class="px-6 py-4">
                <span :class="getStatusBadgeClass(appt.status)" class="px-3 py-1 rounded-full text-xs font-semibold">
                  {{ getStatusLabel(appt.status) }}
                </span>
              </td>
              <td class="px-6 py-4">
                <div class="flex gap-2">
                  <button @click="updateStatus(appt.id, 'CONFIRMED')" 
                          v-if="appt.status === 'SCHEDULED'"
                          class="text-emerald-600 hover:text-emerald-800 text-sm font-medium">
                    ✓ Confirmer
                  </button>
                  <button @click="cancelAppointment(appt.id)" 
                          v-if="appt.status !== 'CANCELLED' && appt.status !== 'COMPLETED'"
                          class="text-red-600 hover:text-red-800 text-sm font-medium">
                    ✕ Annuler
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="appointments.length === 0">
              <td colspan="6" class="px-6 py-8 text-center text-slate-600">
                <span class="text-2xl block mb-2">📭</span>
                Aucun rendez-vous trouvé
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Modal -->
      <div v-if="showAddModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div class="bg-white rounded-xl shadow-xl w-full max-w-md">
          <div class="px-6 py-4 border-b border-slate-200 flex justify-between items-center">
            <h2 class="text-xl font-bold text-slate-900">Nouveau Rendez-vous</h2>
            <button @click="showAddModal = false" class="text-slate-600 hover:text-slate-900 text-2xl">
              ✕
            </button>
          </div>
          
          <form @submit.prevent="addAppointment" class="p-6 space-y-4">
            <!-- Patient ID -->
            <div>
              <label class="block text-sm font-medium text-slate-900 mb-2">ID Patient</label>
              <input v-model="newAppt.patient_id" type="number" placeholder="123" required
                     class="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent" />
            </div>

            <!-- Doctor ID -->
            <div>
              <label class="block text-sm font-medium text-slate-900 mb-2">ID Médecin</label>
              <input v-model="newAppt.doctor_id" type="number" placeholder="456" required
                     class="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent" />
            </div>

            <!-- Service ID -->
            <div>
              <label class="block text-sm font-medium text-slate-900 mb-2">ID Service</label>
              <input v-model="newAppt.service_id" type="number" placeholder="1"
                     class="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent" />
            </div>

            <!-- Date and Time -->
            <div>
              <label class="block text-sm font-medium text-slate-900 mb-2">Date et Heure</label>
              <input v-model="newAppt.appointment_date" type="datetime-local" required
                     class="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent" />
              <p class="text-xs text-slate-500 mt-1">⚠️ Minimum 2 heures à partir de maintenant</p>
            </div>

            <!-- Modal Actions -->
            <div class="flex gap-3 pt-4">
              <button type="button" @click="showAddModal = false" 
                      class="flex-1 px-4 py-2 text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg font-medium transition">
                Annuler
              </button>
              <button type="submit" 
                      class="flex-1 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg font-medium transition">
                Enregistrer
              </button>
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

const appointments = ref([]);
const showAddModal = ref(false);
const loading = ref(false);
const errorMessage = ref('');
const successMessage = ref('');

const newAppt = ref({
  patient_id: '',
  doctor_id: '',
  appointment_date: '',
  service_id: ''
});

const formatDateTime = (dateStr) => {
  try {
    const date = new Date(dateStr);
    return date.toLocaleString('fr-FR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch {
    return dateStr;
  }
};

const getStatusLabel = (status) => {
  const labels = {
    'SCHEDULED': 'Planifié',
    'CONFIRMED': 'Confirmé',
    'CANCELLED': 'Annulé',
    'COMPLETED': 'Terminé'
  };
  return labels[status] || status;
};

const getStatusBadgeClass = (status) => {
  if (status === 'CONFIRMED') return 'bg-emerald-100 text-emerald-700';
  if (status === 'CANCELLED') return 'bg-red-100 text-red-700';
  if (status === 'COMPLETED') return 'bg-blue-100 text-blue-700';
  return 'bg-amber-100 text-amber-700';
};

const fetchAppointments = async () => {
  loading.value = true;
  try {
    const response = await api.instance.get('/clinical/appointments/');
    appointments.value = response.data.appointments || [];
  } catch (error) {
    errorMessage.value = 'Erreur lors du chargement des rendez-vous.';
    console.error('Erreur:', error);
  } finally {
    loading.value = false;
  }
};

const addAppointment = async () => {
  errorMessage.value = '';
  successMessage.value = '';

  try {
    // Validation basique côté client
    if (!newAppt.value.patient_id || !newAppt.value.doctor_id || !newAppt.value.appointment_date) {
      throw new Error('Tous les champs requis doivent être remplis.');
    }

    await api.instance.post('/clinical/appointments/', {
      patient_id: parseInt(newAppt.value.patient_id),
      doctor_id: parseInt(newAppt.value.doctor_id),
      appointment_date: newAppt.value.appointment_date,
      service_id: newAppt.value.service_id ? parseInt(newAppt.value.service_id) : null
    });

    successMessage.value = '✅ Rendez-vous enregistré avec succès !';
    showAddModal.value = false;
    newAppt.value = { patient_id: '', doctor_id: '', appointment_date: '', service_id: '' };
    await fetchAppointments();
  } catch (error) {
    // Gestion détaillée des erreurs
    if (error.response?.data?.detail) {
      errorMessage.value = error.response.data.detail;
    } else if (error.response?.data) {
      // Traiter les erreurs multiples du formulaire
      const errorLines = Object.entries(error.response.data)
        .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(', ') : value}`)
        .join('\n');
      errorMessage.value = errorLines || 'Une erreur est survenue.';
    } else if (error.message) {
      errorMessage.value = error.message;
    } else {
      errorMessage.value = 'Une erreur inconnue s\'est produite.';
    }
  }
};

const updateStatus = async (appointmentId, newStatus) => {
  try {
    await api.instance.patch(`/clinical/appointments/${appointmentId}/`, {
      status: newStatus
    });
    successMessage.value = '✅ Rendez-vous mis à jour avec succès !';
    await fetchAppointments();
  } catch (error) {
    errorMessage.value = error.response?.data?.detail || 'Erreur lors de la mise à jour.';
  }
};

const cancelAppointment = async (appointmentId) => {
  if (!confirm('Êtes-vous sûr de vouloir annuler ce rendez-vous ?')) return;
  await updateStatus(appointmentId, 'CANCELLED');
};

onMounted(() => {
  fetchAppointments();
});
</script>