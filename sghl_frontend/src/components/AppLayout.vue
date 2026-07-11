<template>
  <div class="flex h-screen bg-slate-50">
    <aside class="w-64 bg-slate-900 text-white shadow-lg">
      <div class="p-6 text-xl font-bold text-emerald-500">SGHL Portal</div>
      <p class="px-6 text-sm text-slate-400">{{ roleLabel }}</p>
      <nav class="mt-6">
        <router-link :to="dashboardRoute" class="block py-3 px-6 hover:bg-slate-800 border-l-4 border-transparent hover:border-emerald-500">Tableau de bord</router-link>
        <router-link to="/appointments" class="block py-3 px-6 hover:bg-slate-800 border-l-4 border-transparent hover:border-emerald-500">Rendez-vous</router-link>
        <router-link to="/chat" class="block py-3 px-6 hover:bg-slate-800 border-l-4 border-transparent hover:border-emerald-500">Chat interne</router-link>
        <router-link to="/profile" class="block py-3 px-6 hover:bg-slate-800 border-l-4 border-transparent hover:border-emerald-500">Profil</router-link>
      </nav>
      <div class="px-6 mt-8">
        <button class="w-full rounded-lg bg-emerald-600 px-3 py-2 text-sm font-semibold hover:bg-emerald-500" @click="logout">Déconnexion</button>
      </div>
    </aside>

    <main class="flex-1 p-8 overflow-y-auto">
      <slot />
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();

const userData = computed(() => JSON.parse(localStorage.getItem('user') || '{}'));
const roleLabel = computed(() => {
  const role = (userData.value.role || '').toUpperCase();
  if (role === 'DOCTOR') return 'Médecin';
  if (role === 'PATIENT') return 'Patient';
  if (role === 'SECRETARY' || role === 'SECRETARY_GENERAL' || role === 'SECRETARY_SERVICE') return 'Secrétaire';
  if (role === 'ADMIN') return 'Administrateur';
  return 'Utilisateur';
});

const dashboardRoute = computed(() => {
  const role = (userData.value.role || '').toUpperCase();
  if (role === 'DOCTOR') return '/dashboard/doctor';
  if (role === 'ADMIN') return '/dashboard/admin';
  if (role === 'SECRETARY' || role === 'SECRETARY_GENERAL' || role === 'SECRETARY_SERVICE') return '/dashboard/secretary';
  return '/dashboard/patient';
});

const logout = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  router.push('/login');
};
</script>