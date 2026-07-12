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

      <nav class="mt-6 flex-1 space-y-1 px-3 overflow-y-auto">
        <router-link :to="dashboardRoute" class="group flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium text-slate-300 transition-all duration-200 hover:bg-white/10 hover:text-white" active-class="bg-emerald-500/15 text-white shadow-sm">
          <span>📊</span> Table de bord
        </router-link>

        <div v-if="isAdmin" class="mt-4 px-4 text-[10px] font-bold uppercase text-slate-500 tracking-wider">Gestion Globale</div>
        
        <router-link v-if="isAdmin" to="/patients" class="group flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium text-slate-300 transition-all duration-200 hover:bg-white/10 hover:text-white" active-class="bg-emerald-500/15 text-white shadow-sm">
          <span>📁</span> Dossiers Patients
        </router-link>
        <router-link v-if="isAdmin" to="/laboratory" class="group flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium text-slate-300 transition-all duration-200 hover:bg-white/10 hover:text-white" active-class="bg-emerald-500/15 text-white shadow-sm">
          <span>🧪</span> Laboratoire
        </router-link>
        <router-link v-if="isAdmin" to="/pharmacy" class="group flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium text-slate-300 transition-all duration-200 hover:bg-white/10 hover:text-white" active-class="bg-emerald-500/15 text-white shadow-sm">
          <span>💊</span> Pharmacie & Stocks
        </router-link>
        <router-link v-if="isAdmin" to="/payments" class="group flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium text-slate-300 transition-all duration-200 hover:bg-white/10 hover:text-white" active-class="bg-emerald-500/15 text-white shadow-sm">
          <span>💳</span> Facturation & Paiements
        </router-link>
        <router-link v-if="isAdmin" to="/visitors" class="group flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium text-slate-300 transition-all duration-200 hover:bg-white/10 hover:text-white" active-class="bg-emerald-500/15 text-white shadow-sm">
          <span>📍</span> Localisation Visites
        </router-link>
        <router-link v-if="isAdmin" to="/pediatrie" class="group flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium text-slate-300 transition-all duration-200 hover:bg-white/10 hover:text-white" active-class="bg-emerald-500/15 text-white shadow-sm">
        <span>👶</span> Pédiatrie
        </router-link>
        <router-link v-if="isAdmin" to="/staff" class="group flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium text-slate-300 transition-all duration-200 hover:bg-white/10 hover:text-white" active-class="bg-emerald-500/15 text-white shadow-sm">
        <span>👥</span> Gestion du Staff
        </router-link>


        <div class="mt-4 px-4 text-[10px] font-bold uppercase text-slate-500 tracking-wider">Communication</div>
        <router-link to="/appointments" class="group flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium text-slate-300 transition-all duration-200 hover:bg-white/10 hover:text-white" active-class="bg-emerald-500/15 text-white shadow-sm">
          <span>📅</span> Rendez-vous
        </router-link>
        <router-link to="/chat" class="group flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium text-slate-300 transition-all duration-200 hover:bg-white/10 hover:text-white" active-class="bg-emerald-500/15 text-white shadow-sm">
          <span>💬</span> Chat interne
        </router-link>
        <router-link to="/profile" class="group flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium text-slate-300 transition-all duration-200 hover:bg-white/10 hover:text-white" active-class="bg-emerald-500/15 text-white shadow-sm">
          <span>👤</span> Profil
        </router-link>
      </nav>

      <div class="border-t border-white/10 p-4">
        <button class="group w-full rounded-xl bg-emerald-600 px-3 py-2 text-sm font-semibold text-white transition hover:bg-emerald-500" @click="logout">
          ↪ Déconnexion
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

// Détection Admin
const isAdmin = computed(() => userData.value.role === 'ADMIN');

const roleLabel = computed(() => {
  const role = (userData.value.role || '').toUpperCase();
  if (role === 'ADMIN') return 'Super Administrateur';
  return role;
});

const dashboardRoute = computed(() => {
  const role = (userData.value.role || '').toUpperCase();
  if (role === 'ADMIN') return '/dashboard/admin';
  return '/dashboard';
});

const logout = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  router.push('/login');
};
</script>