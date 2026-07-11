<template>
  <AppLayout>
    <div class="p-6 max-w-2xl">
      <h1 class="text-2xl font-bold text-slate-800 mb-6">⚙️ Paramètres</h1>
      
      <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200 space-y-6">
        <div>
          <label class="block font-medium text-slate-700">Nom de l'établissement</label>
          <input type="text" class="w-full border p-2 rounded mt-1" value="SGHL Pointe-Noire" />
        </div>
        <div>
          <label class="block font-medium text-slate-700">Seuil d'alerte des rendez-vous (jours)</label>
          <input type="number" class="w-full border p-2 rounded mt-1" value="3" />
        </div>
        <button class="bg-green-600 text-white px-6 py-2 rounded-lg font-bold">Enregistrer les modifications</button>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import AppLayout from '@/components/AppLayout.vue';
</script>