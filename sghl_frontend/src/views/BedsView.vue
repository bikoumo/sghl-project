<template>
  <AppLayout>
    <div class="beds-page">
      <header class="beds-hero">
        <div>
          <p class="beds-hero__eyebrow">Hospitalisation</p>
          <h1 class="beds-hero__title">Gestion des lits &amp; admissions</h1>
          <p class="beds-hero__lead">Occupation en temps réel, admissions et sorties patients.</p>
        </div>
        <div class="beds-hero__stats">
          <div class="stat stat--total">
            <span class="stat__value">{{ beds.length }}</span>
            <span class="stat__label">Lits</span>
          </div>
          <div class="stat stat--free">
            <span class="stat__value">{{ freeCount }}</span>
            <span class="stat__label">Libres</span>
          </div>
          <div class="stat stat--busy">
            <span class="stat__value">{{ occupiedCount }}</span>
            <span class="stat__label">Occupés</span>
          </div>
          <button type="button" class="beds-refresh" :disabled="loading" @click="fetchBeds">
            <span :class="{ 'is-spinning': loading }">⟳</span> Actualiser
          </button>
        </div>
      </header>

      <div v-if="occupationRate !== null" class="beds-gauge">
        <div class="beds-gauge__track">
          <div class="beds-gauge__fill" :style="{ width: `${occupationRate}%` }"></div>
        </div>
        <span class="beds-gauge__label">Taux d'occupation : {{ occupationRate }}%</span>
      </div>

      <div v-if="errorMessage" class="alert alert--error">{{ errorMessage }}</div>
      <div v-if="successMessage" class="alert alert--success">{{ successMessage }}</div>

      <div class="beds-toolbar">
        <div class="beds-filters">
          <button
            v-for="opt in filterOptions"
            :key="opt.value"
            type="button"
            class="chip"
            :class="{ 'chip--active': statusFilter === opt.value }"
            @click="statusFilter = opt.value"
          >
            {{ opt.label }}
          </button>
        </div>
        <select v-if="serviceOptions.length > 1" v-model="serviceFilter" class="beds-service-select">
          <option value="">Tous les services</option>
          <option v-for="s in serviceOptions" :key="s" :value="s">{{ s }}</option>
        </select>
      </div>

      <div v-if="loading" class="beds-grid">
        <div v-for="n in 6" :key="n" class="bed-card bed-card--skeleton" />
      </div>

      <div v-else-if="!beds.length" class="beds-empty">
        Aucun lit dans votre périmètre. Vérifiez le seed démo ou votre service.
      </div>

      <div v-else-if="!filteredBeds.length" class="beds-empty">
        Aucun lit ne correspond au filtre sélectionné.
      </div>

      <div v-else class="beds-grid">
        <article
          v-for="bed in filteredBeds"
          :key="bed.id"
          class="bed-card"
          :class="bed.is_occupied ? 'bed-card--busy' : 'bed-card--free'"
        >
          <div class="bed-card__top">
            <div>
              <h3 class="bed-card__title">Lit {{ bed.number }}</h3>
              <p class="bed-card__sub">Chambre {{ bed.room_number }} · {{ bed.service_name }}</p>
            </div>
            <span class="bed-status" :class="bed.is_occupied ? 'bed-status--busy' : 'bed-status--free'">
              {{ bed.is_occupied ? 'Occupé' : 'Libre' }}
            </span>
          </div>

          <div v-if="bed.is_occupied" class="bed-card__body">
            <div class="bed-row">
              <span class="bed-row__key">Patient</span>
              <span class="bed-row__val">{{ bed.patient_name || '—' }}</span>
            </div>
            <div v-if="bed.patient_matricule" class="bed-row">
              <span class="bed-row__key">Matricule</span>
              <span class="bed-row__val">{{ bed.patient_matricule }}</span>
            </div>
            <div class="bed-row">
              <span class="bed-row__key">Médecin</span>
              <span class="bed-row__val">{{ bed.doctor_name || '—' }}</span>
            </div>
            <div v-if="bed.admission_date" class="bed-row">
              <span class="bed-row__key">Depuis</span>
              <span class="bed-row__val">{{ formatDuration(bed.admission_date) }}</span>
            </div>
            <p v-if="bed.reason" class="bed-reason">« {{ bed.reason }} »</p>
          </div>
          <p v-else class="bed-card__ready">Prêt pour une nouvelle admission.</p>

          <div class="bed-card__actions">
            <button
              v-if="!bed.is_occupied"
              type="button"
              class="btn btn--admit"
              :disabled="actionLoading"
              @click="openAdmitModal(bed)"
            >
              Admettre un patient
            </button>
            <button
              v-else
              type="button"
              class="btn btn--release"
              :disabled="actionLoading"
              @click="releaseBed(bed)"
            >
              Libérer le lit
            </button>
          </div>
        </article>
      </div>

      <!-- Modal admission -->
      <div v-if="admitBed" class="modal-overlay" @click.self="closeAdmitModal">
        <div class="modal">
          <div class="modal__head">
            <div>
              <h2 class="modal__title">Admission — Lit {{ admitBed.number }}</h2>
              <p class="modal__sub">{{ admitBed.service_name }} · Chambre {{ admitBed.room_number }}</p>
            </div>
            <button type="button" class="modal__close" :disabled="actionLoading" @click="closeAdmitModal">✕</button>
          </div>

          <form class="modal__form" @submit.prevent="submitAdmit">
            <div class="field">
              <label for="patient">Patient</label>
              <select id="patient" v-model.number="admitForm.patient_id" required>
                <option :value="0" disabled>Sélectionner un patient</option>
                <option v-for="p in patients" :key="p.id" :value="p.id">
                  {{ p.nom }} {{ p.prenom }} ({{ p.matricule }})
                </option>
              </select>
            </div>

            <div v-if="!isDoctor" class="field">
              <label for="doctor">Médecin référent</label>
              <select id="doctor" v-model.number="admitForm.doctor_id" required>
                <option :value="0" disabled>Sélectionner un médecin</option>
                <option v-for="d in doctors" :key="d.id" :value="d.id">
                  Dr {{ d.prenom }} {{ d.nom }}
                </option>
              </select>
            </div>

            <div class="field">
              <label for="reason">Motif d'hospitalisation</label>
              <textarea
                id="reason"
                v-model="admitForm.reason"
                rows="3"
                required
                minlength="3"
                maxlength="500"
                placeholder="Décrivez le motif d'admission..."
              />
            </div>

            <p v-if="formError" class="modal__error">{{ formError }}</p>

            <div class="modal__actions">
              <button type="button" class="btn btn--ghost" :disabled="actionLoading" @click="closeAdmitModal">
                Annuler
              </button>
              <button type="submit" class="btn btn--admit" :disabled="actionLoading">
                {{ actionLoading ? 'Admission…' : 'Confirmer l\'admission' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue';
import AppLayout from '@/components/AppLayout.vue';
import api from '@/api';

const beds = ref([]);
const patients = ref([]);
const doctors = ref([]);
const loading = ref(true);
const actionLoading = ref(false);
const errorMessage = ref('');
const successMessage = ref('');
const formError = ref('');
const admitBed = ref(null);
const statusFilter = ref('all');
const serviceFilter = ref('');
const admitForm = reactive({
  patient_id: 0,
  doctor_id: 0,
  reason: '',
});

const filterOptions = [
  { value: 'all', label: 'Tous' },
  { value: 'free', label: 'Libres' },
  { value: 'busy', label: 'Occupés' },
];

const user = JSON.parse(localStorage.getItem('user') || '{}');
const isDoctor = computed(() => (user.role || '').toUpperCase() === 'DOCTOR');

const freeCount = computed(() => beds.value.filter((b) => !b.is_occupied).length);
const occupiedCount = computed(() => beds.value.filter((b) => b.is_occupied).length);
const occupationRate = computed(() => {
  if (!beds.value.length) return null;
  return Math.round((occupiedCount.value / beds.value.length) * 100);
});

const serviceOptions = computed(() => {
  const set = new Set(beds.value.map((b) => b.service_name).filter(Boolean));
  return [...set].sort();
});

const filteredBeds = computed(() => {
  return beds.value.filter((b) => {
    if (statusFilter.value === 'free' && b.is_occupied) return false;
    if (statusFilter.value === 'busy' && !b.is_occupied) return false;
    if (serviceFilter.value && b.service_name !== serviceFilter.value) return false;
    return true;
  });
});

const formatDuration = (dateStr) => {
  try {
    const start = new Date(dateStr);
    const now = new Date();
    const diffMs = now - start;
    const days = Math.floor(diffMs / 86400000);
    const hours = Math.floor((diffMs % 86400000) / 3600000);
    if (days > 0) return `${days} j ${hours} h`;
    if (hours > 0) return `${hours} h`;
    const mins = Math.max(1, Math.floor(diffMs / 60000));
    return `${mins} min`;
  } catch {
    return '—';
  }
};

const apiError = (error, fallback) =>
  error?.response?.data?.detail ||
  error?.response?.data?.message ||
  fallback;

const fetchBeds = async () => {
  loading.value = true;
  errorMessage.value = '';
  try {
    const response = await api.instance.get('/clinical/beds/');
    beds.value = Array.isArray(response.data) ? response.data : [];
  } catch (error) {
    beds.value = [];
    errorMessage.value = apiError(error, 'Impossible de charger les lits.');
  } finally {
    loading.value = false;
  }
};

const fetchPatientsAndDoctors = async () => {
  try {
    const [patientsRes, doctorsRes] = await Promise.all([
      api.instance.get('/clinical/patients'),
      api.instance.get('/clinical/doctors'),
    ]);
    patients.value = Array.isArray(patientsRes.data) ? patientsRes.data : [];
    doctors.value = Array.isArray(doctorsRes.data) ? doctorsRes.data : [];
  } catch (error) {
    console.error(error);
  }
};

const openAdmitModal = (bed) => {
  admitBed.value = bed;
  admitForm.patient_id = 0;
  admitForm.doctor_id = 0;
  admitForm.reason = '';
  formError.value = '';
  successMessage.value = '';
};

const closeAdmitModal = () => {
  if (actionLoading.value) return;
  admitBed.value = null;
  formError.value = '';
};

const submitAdmit = async () => {
  formError.value = '';
  if (!admitForm.patient_id) {
    formError.value = 'Sélectionnez un patient.';
    return;
  }
  if (!isDoctor.value && !admitForm.doctor_id) {
    formError.value = 'Sélectionnez un médecin référent.';
    return;
  }
  if ((admitForm.reason || '').trim().length < 3) {
    formError.value = 'Le motif doit contenir au moins 3 caractères.';
    return;
  }

  actionLoading.value = true;
  try {
    const payload = {
      patient_id: admitForm.patient_id,
      reason: admitForm.reason.trim(),
    };
    if (!isDoctor.value) {
      payload.doctor_id = admitForm.doctor_id;
    }
    const response = await api.instance.post(`/clinical/beds/${admitBed.value.id}/admit`, payload);
    const updated = response.data;
    beds.value = beds.value.map((b) => (b.id === updated.id ? updated : b));
    successMessage.value = `Patient admis sur le lit ${updated.number}.`;
    admitBed.value = null;
  } catch (error) {
    formError.value = apiError(error, "Impossible d'admettre le patient.");
  } finally {
    actionLoading.value = false;
  }
};

const releaseBed = async (bed) => {
  const ok = window.confirm(`Libérer le lit ${bed.number} (patient : ${bed.patient_name || 'N/A'}) ?`);
  if (!ok) return;

  actionLoading.value = true;
  errorMessage.value = '';
  successMessage.value = '';
  try {
    const response = await api.instance.post(`/clinical/beds/${bed.id}/release`);
    const updated = response.data;
    beds.value = beds.value.map((b) => (b.id === updated.id ? updated : b));
    successMessage.value = `Lit ${updated.number} libéré.`;
  } catch (error) {
    errorMessage.value = apiError(error, 'Impossible de libérer le lit.');
  } finally {
    actionLoading.value = false;
  }
};

onMounted(async () => {
  await Promise.all([fetchBeds(), fetchPatientsAndDoctors()]);
});
</script>

<style scoped>
.beds-page {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  animation: sghl-fade-up 0.4s ease both;
}

/* Hero */
.beds-hero {
  display: flex;
  flex-wrap: wrap;
  gap: 1.5rem;
  justify-content: space-between;
  align-items: flex-end;
  padding: 1.5rem 1.75rem;
  border-radius: 18px;
  color: #f8fafc;
  background:
    radial-gradient(ellipse at 90% 10%, rgba(96, 165, 250, 0.22), transparent 45%),
    linear-gradient(135deg, #071535 0%, #0b1f4a 55%, #1e3a8a 130%);
  border: 1px solid rgba(147, 197, 253, 0.15);
}
.beds-hero__eyebrow {
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: #93c5fd;
}
.beds-hero__title {
  margin-top: 0.35rem;
  font-size: 1.7rem;
  font-weight: 800;
  color: #fff;
  letter-spacing: -0.02em;
}
.beds-hero__lead {
  margin-top: 0.3rem;
  font-size: 0.92rem;
  color: rgba(226, 232, 240, 0.82);
}
.beds-hero__stats {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}
.stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 68px;
  padding: 0.55rem 0.85rem;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
}
.stat__value {
  font-size: 1.5rem;
  font-weight: 800;
  line-height: 1;
  color: #fff;
}
.stat__label {
  margin-top: 0.2rem;
  font-size: 0.72rem;
  font-weight: 600;
  color: rgba(226, 232, 240, 0.8);
}
.stat--free .stat__value { color: #6ee7b7; }
.stat--busy .stat__value { color: #fca5a5; }

.beds-refresh {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.6rem 1rem;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 650;
  color: #0b1f4a;
  background: #e0e9f9;
  border: none;
  cursor: pointer;
  transition: background 0.15s ease;
}
.beds-refresh:hover:not(:disabled) { background: #fff; }
.beds-refresh:disabled { opacity: 0.6; cursor: not-allowed; }
.is-spinning { display: inline-block; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* Gauge */
.beds-gauge {
  display: flex;
  align-items: center;
  gap: 0.9rem;
}
.beds-gauge__track {
  flex: 1;
  height: 10px;
  border-radius: 999px;
  background: #dbe3f1;
  overflow: hidden;
}
.beds-gauge__fill {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, #1e3a8a, #2563eb);
  transition: width 0.4s ease;
}
.beds-gauge__label {
  font-size: 0.82rem;
  font-weight: 700;
  color: #1e3a8a;
  white-space: nowrap;
}

/* Alerts */
.alert {
  padding: 0.8rem 1rem;
  border-radius: 12px;
  font-size: 0.9rem;
  font-weight: 500;
}
.alert--error { background: #fef2f2; color: #b91c1c; border: 1px solid rgba(185, 28, 28, 0.18); }
.alert--success { background: #eff6ff; color: #1e3a8a; border: 1px solid rgba(30, 58, 138, 0.16); }

/* Toolbar */
.beds-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  justify-content: space-between;
  align-items: center;
}
.beds-filters { display: flex; gap: 0.5rem; }
.chip {
  padding: 0.5rem 1rem;
  border-radius: 999px;
  font-size: 0.85rem;
  font-weight: 650;
  color: #475569;
  background: #fff;
  border: 1px solid #dbe3f1;
  cursor: pointer;
  transition: all 0.15s ease;
}
.chip:hover { border-color: #93c5fd; }
.chip--active {
  color: #fff;
  background: #0b1f4a;
  border-color: #0b1f4a;
}
.beds-service-select {
  padding: 0.55rem 0.9rem;
  border-radius: 10px;
  border: 1px solid #dbe3f1;
  background: #fff;
  color: #0b1f4a;
  font-size: 0.85rem;
  font-weight: 600;
}

/* Grid + cards */
.beds-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 1.1rem;
}
.bed-card {
  border-radius: 16px;
  padding: 1.25rem;
  background: #fff;
  border: 1px solid #e2e8f0;
  box-shadow: 0 8px 22px rgba(11, 31, 74, 0.06);
  transition: transform 0.18s ease, box-shadow 0.18s ease;
  display: flex;
  flex-direction: column;
}
.bed-card:hover { transform: translateY(-3px); box-shadow: 0 14px 30px rgba(11, 31, 74, 0.12); }
.bed-card--free { border-top: 4px solid #10b981; }
.bed-card--busy { border-top: 4px solid #ef4444; }
.bed-card--skeleton {
  height: 210px;
  border-top: 4px solid #e2e8f0;
  background: linear-gradient(100deg, #f1f5f9 30%, #e2e8f0 50%, #f1f5f9 70%);
  background-size: 200% 100%;
  animation: sghl-shimmer 1.3s ease-in-out infinite;
}
.bed-card__top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 0.75rem;
}
.bed-card__title {
  font-size: 1.15rem;
  font-weight: 800;
  color: #0b1f4a;
}
.bed-card__sub {
  margin-top: 0.15rem;
  font-size: 0.82rem;
  color: #64748b;
}
.bed-status {
  padding: 0.3rem 0.7rem;
  border-radius: 999px;
  font-size: 0.68rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.bed-status--free { background: #d1fae5; color: #047857; }
.bed-status--busy { background: #fee2e2; color: #b91c1c; }

.bed-card__body {
  margin-top: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  flex: 1;
}
.bed-row {
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
  font-size: 0.86rem;
}
.bed-row__key { color: #64748b; font-weight: 600; }
.bed-row__val { color: #0f172a; font-weight: 650; text-align: right; }
.bed-reason {
  margin-top: 0.4rem;
  padding: 0.55rem 0.7rem;
  border-radius: 8px;
  background: #f1f5f9;
  color: #475569;
  font-size: 0.82rem;
  font-style: italic;
}
.bed-card__ready {
  margin-top: 1rem;
  flex: 1;
  font-size: 0.86rem;
  color: #64748b;
}

.bed-card__actions { margin-top: 1.1rem; }
.btn {
  width: 100%;
  padding: 0.65rem 1rem;
  border-radius: 10px;
  font-size: 0.88rem;
  font-weight: 700;
  border: none;
  cursor: pointer;
  transition: filter 0.15s ease, background 0.15s ease;
}
.btn:disabled { opacity: 0.55; cursor: not-allowed; }
.btn--admit { background: linear-gradient(135deg, #0b1f4a, #2563eb); color: #fff; }
.btn--admit:hover:not(:disabled) { filter: brightness(1.08); }
.btn--release { background: #dc2626; color: #fff; }
.btn--release:hover:not(:disabled) { background: #b91c1c; }
.btn--ghost { background: #f1f5f9; color: #334155; }
.btn--ghost:hover:not(:disabled) { background: #e2e8f0; }

/* Empty */
.beds-empty {
  border: 1px dashed #cbd5e1;
  border-radius: 16px;
  background: #fff;
  padding: 3rem 1.5rem;
  text-align: center;
  color: #64748b;
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  background: rgba(7, 21, 53, 0.55);
  backdrop-filter: blur(3px);
  animation: sghl-fade-up 0.2s ease both;
}
.modal {
  width: 100%;
  max-width: 460px;
  border-radius: 18px;
  background: #fff;
  padding: 1.5rem;
  box-shadow: 0 24px 60px rgba(7, 21, 53, 0.35);
}
.modal__head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
}
.modal__title { font-size: 1.25rem; font-weight: 800; color: #0b1f4a; }
.modal__sub { margin-top: 0.2rem; font-size: 0.85rem; color: #64748b; }
.modal__close {
  border: none;
  background: #f1f5f9;
  color: #475569;
  width: 2rem;
  height: 2rem;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.9rem;
}
.modal__close:hover:not(:disabled) { background: #e2e8f0; }
.modal__form {
  margin-top: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.field { display: flex; flex-direction: column; gap: 0.4rem; }
.field label { font-size: 0.85rem; font-weight: 700; color: #0b1f4a; }
.field select,
.field textarea {
  width: 100%;
  padding: 0.7rem 0.85rem;
  border-radius: 10px;
  border: 1px solid #dbe3f1;
  background: #f8fafc;
  color: #0f172a;
  font-size: 0.9rem;
  outline: none;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}
.field select:focus,
.field textarea:focus {
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15);
  background: #fff;
}
.field textarea { resize: vertical; }
.modal__error { font-size: 0.85rem; color: #dc2626; font-weight: 600; }
.modal__actions { display: flex; gap: 0.75rem; padding-top: 0.25rem; }
.modal__actions .btn { flex: 1; }

@media (max-width: 640px) {
  .beds-hero { align-items: flex-start; }
  .beds-hero__stats { width: 100%; }
}
</style>
