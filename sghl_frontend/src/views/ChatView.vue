<template>
  <AppLayout>
    <div class="space-y-6">
      <header class="rounded-[24px] border border-slate-200 bg-white p-6 shadow-sm">
        <p class="text-sm font-semibold uppercase tracking-[0.24em] text-emerald-600">Communication</p>
        <h1 class="mt-2 text-3xl font-bold text-slate-900">Chat interne</h1>
        <p class="mt-1 text-slate-600">Canal de coordination rapide entre services et équipes hospitalières.</p>
      </header>

      <div class="rounded-[24px] border border-slate-200 bg-white shadow-sm overflow-hidden">
        <div class="bg-[#0b1727] px-6 py-4 text-white">
          <h2 class="text-lg font-semibold">Messages récents</h2>
          <p class="text-sm text-slate-300">Priorité élevée ou communication de service.</p>
        </div>

        <div class="space-y-4 p-6">
          <div v-for="message in messages" :key="message.id" class="rounded-2xl border border-slate-200 p-4" :class="message.is_urgent ? 'bg-amber-50' : 'bg-slate-50'">
            <div class="mb-2 flex items-center justify-between gap-3">
              <div>
                <p class="font-semibold text-slate-900">{{ message.sender }} • {{ message.service || 'Canal central' }}</p>
                <p class="text-sm text-slate-500">{{ message.created_at ? new Date(message.created_at).toLocaleString('fr-FR') : 'À l’instant' }}</p>
              </div>
              <span class="rounded-full px-3 py-1 text-xs font-semibold" :class="message.is_urgent ? 'bg-amber-100 text-amber-700' : 'bg-emerald-100 text-emerald-700'">
                {{ message.is_urgent ? 'Priorité haute' : 'Normal' }}
              </span>
            </div>
            <p class="text-sm text-slate-700">{{ message.content }}</p>
          </div>

          <div class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <label class="mb-2 block text-sm font-medium text-slate-700" for="message">Nouveau message</label>
            <textarea id="message" v-model="draft" rows="4" class="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none"></textarea>
            <div class="mt-3 flex flex-col gap-3 md:flex-row md:items-center">
              <select v-model="selectedServiceId" class="rounded-xl border border-slate-300 px-3 py-2 text-sm">
                <option :value="null">Canal central</option>
                <option v-for="service in services" :key="service.id" :value="service.id">{{ service.name }}</option>
              </select>
              <label class="flex items-center gap-2 text-sm text-slate-600">
                <input v-model="isUrgent" type="checkbox" />
                Marquer comme urgence
              </label>
            </div>
            <div class="mt-4 flex justify-end">
              <button class="rounded-xl bg-emerald-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-emerald-700" @click="sendMessage">Envoyer</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { onMounted, ref } from 'vue';
import AppLayout from '@/components/AppLayout.vue';
import api from '@/api';

const messages = ref([]);
const services = ref([]);
const draft = ref('');
const selectedServiceId = ref(null);
const isUrgent = ref(false);

const loadMessages = async () => {
  try {
    const response = await api.instance.get('/auth/chat/messages/');
    messages.value = response.data;
  } catch (error) {
    console.error('Chat load failed', error);
  }
};

const loadServices = async () => {
  try {
    const response = await api.instance.get('/auth/services/');
    services.value = response.data;
  } catch (error) {
    console.error('Service load failed', error);
  }
};

const sendMessage = async () => {
  if (!draft.value.trim()) return;
  try {
    await api.instance.post('/auth/chat/messages/', {
      content: draft.value,
      recipient_service_id: selectedServiceId.value,
      is_urgent: isUrgent.value,
    });
    draft.value = '';
    isUrgent.value = false;
    selectedServiceId.value = null;
    await loadMessages();
  } catch (error) {
    console.error('Message send failed', error);
  }
};

onMounted(() => {
  loadMessages();
  loadServices();
});
</script>
