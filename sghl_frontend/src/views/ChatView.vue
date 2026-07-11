<template>
  <AppLayout>
    <div class="min-h-screen bg-slate-50 p-4">
      <div class="max-w-5xl mx-auto bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
        <div class="bg-slate-900 text-white px-6 py-4">
          <h1 class="text-xl font-semibold">Chat interne SGHL</h1>
          <p class="text-sm text-slate-300">Communication urgente entre services</p>
        </div>

        <div class="p-6 space-y-4">
          <div v-for="message in messages" :key="message.id" class="rounded-xl border border-slate-200 p-4" :class="message.is_urgent ? 'bg-amber-50' : 'bg-slate-50'">
            <div class="flex items-center justify-between mb-2">
              <strong>{{ message.sender }} • {{ message.service || 'Canal central' }}</strong>
              <span class="text-xs" :class="message.is_urgent ? 'text-amber-600' : 'text-emerald-600'">{{ message.is_urgent ? 'Priorité haute' : 'Normal' }}</span>
            </div>
            <p class="text-sm text-slate-600">{{ message.content }}</p>
          </div>

          <div class="rounded-xl border border-slate-200 p-4">
            <label class="block text-sm font-medium text-slate-700 mb-2" for="message">Nouveau message</label>
            <textarea id="message" v-model="draft" rows="4" class="w-full rounded-lg border border-slate-300 px-3 py-2"></textarea>
            <div class="flex items-center gap-3 mt-3">
              <select v-model="selectedServiceId" class="rounded-lg border border-slate-300 px-3 py-2">
                <option :value="null">Canal central</option>
                <option v-for="service in services" :key="service.id" :value="service.id">{{ service.name }}</option>
              </select>
              <label class="flex items-center gap-2 text-sm text-slate-600">
                <input v-model="isUrgent" type="checkbox" />
                Urgence
              </label>
            </div>
            <div class="mt-3 flex justify-end">
              <button class="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-500" @click="sendMessage">Envoyer</button>
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
