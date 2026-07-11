<template>
  <AppLayout>
    <div class="page-padding">
      <ConsultationForm />
    </div>
  </AppLayout>
</template>

<script setup>
import AppLayout from '@/components/AppLayout.vue';
import ConsultationForm from '@/views/ConsultationForm.vue';
</script>

<style scoped>
.page-padding { padding: 40px; }
</style>