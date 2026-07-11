<template>
  <div class="flex h-screen bg-[#f4f6fb]">
    <aside class="flex w-72 flex-col bg-[#0b1727] text-white shadow-2xl">
      <div class="border-b border-white/10 px-6 py-6">
        <div class="flex items-center gap-3">
          <div class="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-emerald-400/20 to-cyan-400/20 text-xl shadow-inner text-emerald-400">🏥</div>
          <div>
            <p class="text-lg font-semibold">SGHL Portal</p>
            <p class="text-sm text-slate-400">{{ roleLabel }}</p>
          </div>
        </div>
      </div>

      <nav class="mt-6 flex-1 space-y-1 px-3">
        <router-link :to="dashboardRoute" class="group flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium text-slate-300 transition-all duration-200 hover:bg-white/10 hover:text-white" active-class="bg-emerald-500/15 text-white shadow-sm">
          <span class="flex h-8 w-8 items-center justify-center rounded-lg bg-white/10 text-sm transition group-hover:scale-105">📊</span>
          <span>Tableau de bord</span>
        </router-link>
        <router-link to="/appointments" class="group flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium text-slate-300 transition-all duration-200 hover:bg-white/10 hover:text-white" active-class="bg-emerald-500/15 text-white shadow-sm">
          <span class="flex h-8 w-8 items-center justify-center rounded-lg bg-white/10 text-sm transition group-hover:scale-105">📅</span>
          <span>Rendez-vous</span>
        </router-link>
        <router-link to="/chat" class="group flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium text-slate-300 transition-all duration-200 hover:bg-white/10 hover:text-white" active-class="bg-emerald-500/15 text-white shadow-sm">
          <span class="flex h-8 w-8 items-center justify-center rounded-lg bg-white/10 text-sm transition group-hover:scale-105">💬</span>
          <span>Chat interne</span>
        </router-link>
        <router-link to="/profile" class="group flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium text-slate-300 transition-all duration-200 hover:bg-white/10 hover:text-white" active-class="bg-emerald-500/15 text-white shadow-sm">
          <span class="flex h-8 w-8 items-center justify-center rounded-lg bg-white/10 text-sm transition group-hover:scale-105">👤</span>
          <span>Profil</span>
        </router-link>
      </nav>

      <div class="border-t border-white/10 p-4">
        <button class="group w-full rounded-xl bg-emerald-600 px-3 py-2 text-sm font-semibold text-white transition hover:bg-emerald-500" @click="logout">
          <span class="mr-2 transition group-hover:translate-x-0.5">↪</span> Déconnexion
        </button>
      </div>
    </aside>

    <main class="flex-1 overflow-y-auto bg-[radial-gradient(circle_at_top_left,_rgba(16,185,129,0.08),_transparent_28%),linear-gradient(180deg,_#f8fafc_0%,_#f4f6fb_100%)] p-6 lg:p-8">
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