<template>
  <AppLayout>
    <div class="space-y-6">
      <header class="rounded-[24px] border border-slate-200 bg-white p-6 shadow-sm">
        <p class="text-sm font-semibold uppercase tracking-[0.24em] text-emerald-600">Profil</p>
        <h1 class="mt-2 text-3xl font-bold text-slate-900">Mon profil</h1>
        <p class="mt-1 text-slate-600">Vue d’ensemble du compte, des informations médicales et du tableau de bord de service.</p>
      </header>

      <div class="overflow-hidden rounded-[24px] border border-slate-200 bg-white shadow-sm">
        <div class="flex flex-col gap-6 bg-gradient-to-r from-[#0b1727] via-[#11263d] to-[#1b3d5f] px-8 py-6 md:flex-row md:items-center md:justify-between">
          <div class="flex items-center gap-4">
            <img v-if="user.has_picture" :src="user.avatar" class="h-20 w-20 rounded-full border-4 border-white object-cover" />
            <div v-else class="flex h-20 w-20 items-center justify-center rounded-full border-4 border-white bg-slate-700 text-2xl font-bold text-white">
              {{ userInitials }}
            </div>
            <div class="text-white">
              <p class="text-xl font-semibold">{{ user.full_name }}</p>
              <p class="text-sm text-slate-300">{{ user.role_label }} · {{ user.service || 'Aucun service' }}</p>
            </div>
          </div>
          <div class="text-sm text-slate-300">
            <p>Email : {{ user.email || 'Non renseigné' }}</p>
            <p>Téléphone : {{ user.phone || 'Non renseigné' }}</p>
          </div>
        </div>

        <div class="grid gap-6 p-8 lg:grid-cols-[1.2fr_0.8fr]">
          <section class="space-y-4">
            <h2 class="text-lg font-semibold text-slate-900">Informations</h2>
            <div class="grid gap-4 md:grid-cols-2">
              <div class="rounded-2xl bg-slate-50 p-4">
                <p class="text-sm text-slate-500">Groupe sanguin</p>
                <p class="mt-1 font-semibold text-slate-900">{{ user.groupe_sanguin || 'Non renseigné' }}</p>
              </div>
              <div class="rounded-2xl bg-slate-50 p-4">
                <p class="text-sm text-slate-500">Allergies</p>
                <p class="mt-1 font-semibold text-slate-900">{{ user.allergies || 'Aucune' }}</p>
              </div>
              <div class="rounded-2xl bg-slate-50 p-4 md:col-span-2">
                <p class="text-sm text-slate-500">Antécédents</p>
                <p class="mt-1 font-semibold text-slate-900">{{ user.antecedents || 'Aucun' }}</p>
              </div>
            </div>
          </section>

          <section class="space-y-4">
            <h2 class="text-lg font-semibold text-slate-900">Tableau de bord</h2>
            <div class="grid gap-3">
              <div v-for="card in dashboardCards" :key="card.label" class="rounded-2xl border border-slate-200 p-4 transition duration-200 hover:-translate-y-0.5 hover:shadow-sm">
                <p class="text-sm text-slate-500">{{ card.label }}</p>
                <p class="mt-2 text-2xl font-semibold text-slate-900">{{ card.value }}</p>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import AppLayout from '@/components/AppLayout.vue';
import api from '@/api';

const user = ref({
  full_name: 'Utilisateur',
  role: '',
  role_label: 'Utilisateur',
  service: '',
  email: '',
  phone: '',
  groupe_sanguin: '',
  allergies: '',
  antecedents: '',
  has_picture: false,
  avatar: ''
});

const dashboardCards = ref([]);

const userInitials = computed(() => {
  const name = user.value.full_name || 'Utilisateur';
  return name.split(' ').map((n) => n[0]).join('').substring(0, 2).toUpperCase();
});

const loadProfile = async () => {
  try {
    const storedUser = JSON.parse(localStorage.getItem('user') || '{}');
    user.value = {
      full_name: storedUser.full_name || storedUser.username || 'Utilisateur',
      role: storedUser.role || 'Inconnu',
      role_label: storedUser.role_label || storedUser.role || 'Utilisateur',
      service: storedUser.service || '',
      email: storedUser.email || '',
      phone: storedUser.phone || '',
      groupe_sanguin: storedUser.groupe_sanguin || '',
      allergies: storedUser.allergies || '',
      antecedents: storedUser.antecedents || '',
      has_picture: storedUser.has_picture || false,
      avatar: storedUser.avatar || ''
    };

    const response = await api.instance.get('/auth/profile/summary/');
    if (response.data?.user) {
      user.value = { ...user.value, ...response.data.user };
      user.value.full_name = response.data.user.full_name || user.value.full_name;
      user.value.role_label = response.data.user.role || user.value.role_label;
      user.value.avatar = response.data.user.has_picture ? '/media/profiles/default.png' : '';
    }

    if (response.data?.kpis) {
      dashboardCards.value = [
        { label: 'Patients en charge', value: response.data.kpis.patients },
        { label: 'Docteurs actifs', value: response.data.kpis.doctors },
        { label: 'Urgences en cours', value: response.data.kpis.urgencies },
        { label: 'Factures en attente', value: response.data.kpis.pending_invoices },
      ];
    }
  } catch (error) {
    console.error('Erreur chargement profil', error);
  }
};

onMounted(() => {
  loadProfile();
});
</script>