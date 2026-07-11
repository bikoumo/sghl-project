<template>
  <AppLayout>
    <div class="p-6">
      <header class="flex justify-between items-center mb-6">
        <div>
          <h1 class="text-2xl font-bold text-slate-800">👥 Gestion du Personnel</h1>
          <p class="text-slate-500">Liste des médecins et infirmiers du service.</p>
        </div>
        <button class="bg-blue-600 text-white px-4 py-2 rounded-lg font-medium">＋ Ajouter Membre</button>
      </header>

      <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <table class="w-full text-left">
          <thead class="text-slate-400 text-sm border-b">
            <tr><th class="pb-3">Nom</th><th class="pb-3">Rôle</th><th class="pb-3">Contact</th></tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr class="text-slate-700">
              <td class="py-4 font-medium">Dr. Jean Dupont</td>
              <td class="py-4">Médecin Chef</td>
              <td class="py-4">jean.dupont@sghl.cg</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import AppLayout from '@/components/AppLayout.vue';
</script>