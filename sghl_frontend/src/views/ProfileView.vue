<template>
  <AppLayout>
    <div class="p-6 max-w-2xl mx-auto">
      <header class="mb-8">
        <h1 class="text-2xl font-bold text-slate-800">👤 Mon Profil</h1>
      </header>

      <div class="bg-white p-8 rounded-xl shadow-sm border border-slate-200 flex flex-col md:flex-row items-center gap-8">
        <div class="w-24 h-24 bg-blue-600 text-white flex items-center justify-center rounded-full font-bold text-3xl shadow-inner">
          {{ userInitials }}
        </div>

        <div class="flex-1 space-y-4 w-full">
          <div>
            <label class="text-slate-400 text-xs uppercase font-bold">Nom complet</label>
            <p class="text-lg font-medium text-slate-800">{{ user.full_name }}</p>
          </div>
          <div>
            <label class="text-slate-400 text-xs uppercase font-bold">Rôle</label>
            <p class="text-lg font-medium text-slate-800">{{ user.role }}</p>
          </div>
          <div>
            <label class="text-slate-400 text-xs uppercase font-bold">Service</label>
            <p class="text-lg font-medium text-slate-800">{{ user.service || 'Aucun' }}</p>
          </div>
          <div>
            <label class="text-slate-400 text-xs uppercase font-bold">Email</label>
            <p class="text-lg font-medium text-slate-800">{{ user.email }}</p>
          </div>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import AppLayout from '@/components/AppLayout.vue';

const user = ref({
  full_name: '',
  role: '',
  service: '',
  email: ''
});

const userInitials = computed(() => {
  const name = user.value.full_name || 'Utilisateur';
  return name.split(' ').map((n) => n[0]).join('').substring(0, 2).toUpperCase();
});

onMounted(() => {
  try {
    const storedUser = JSON.parse(localStorage.getItem('user') || '{}');
    user.value = {
      full_name: storedUser.username || 'Utilisateur',
      role: storedUser.role || 'Inconnu',
      service: storedUser.service || '',
      email: storedUser.email || ''
    };
  } catch (error) {
    console.error('Erreur chargement profil', error);
  }
});
</script>