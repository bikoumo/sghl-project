<template>
  <AppLayout>
    <div class="max-w-2xl mx-auto mt-10">
      <div class="bg-white p-8 rounded-2xl shadow-xl border border-slate-200">
        <h1 class="text-3xl font-bold text-slate-900 mb-6">À propos de SGHL</h1>
        
        <div class="space-y-4 text-slate-600">
          <p><strong>Système de Gestion Hospitalière Logistique (SGHL)</strong> est une solution logicielle innovante conçue pour moderniser la gestion des structures de santé princalement en Afrique .</p>
          <p>Version : 1.0.0</p>
          <p>Date de création : Juin 2026 pour un projet de fin d'études(GI3)</p>
          <hr class="my-4">
          <p><strong>Développé par :</strong> Theresa Dinilie Bikoumou</p>
          <p>Contact : bikoumoutheresa@gmail.com / +242 05 390 94 85</p>
        </div>

        <div class="mt-8">
          <Button @click="$router.push('/')">Retour au Dashboard</Button>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import AppLayout from '@/components/AppLayout.vue';
import Button from '@/components/ui/Button.vue';
</script>