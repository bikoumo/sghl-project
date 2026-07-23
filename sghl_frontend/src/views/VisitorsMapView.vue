<template>
  <AppLayout>
    <div class="min-h-screen bg-slate-50">
      <!-- Header -->
      <div class="bg-white border-b border-slate-200">
        <div class="max-w-7xl mx-auto px-6 py-8">
          <h1 class="text-3xl font-bold text-slate-900">🗺️ Localisation des Services</h1>
          <p class="text-slate-600 mt-1">Guide de navigation pour les visiteurs</p>
        </div>
      </div>

      <!-- Main Content -->
      <div class="max-w-7xl mx-auto px-6 py-8">
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          <!-- Map Container (Left side) -->
          <div class="lg:col-span-2">
            <div class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
              <!-- Map embedded with Leaflet (open-source) -->
              <div id="map-container" class="w-full h-96 md:h-96 lg:h-full rounded-lg border-2 border-slate-300">
                <div class="w-full h-full flex items-center justify-center bg-slate-100">
                  <div class="text-center">
                    <span class="text-5xl block mb-3">🗺️</span>
                    <p class="text-slate-600">
                      <strong>Intégration Leaflet / OpenStreetMap</strong><br>
                      Remplacez cette section par une véritable carte interactive<br>
                      avec points de localisation GPS (latitude/longitude)
                    </p>
                    <div class="mt-4 inline-block bg-blue-100 text-blue-900 px-4 py-2 rounded-lg text-sm">
                      💡 Exemple: Centre (latitude: 3.8667, longitude: 11.5167)
                    </div>
                  </div>
                </div>
              </div>

              <!-- Map Info Box -->
              <div class="bg-slate-50 border-t border-slate-200 p-4">
                <div class="flex items-center gap-2 text-sm text-slate-600">
                  <span>📍</span>
                  <span>Cliquez sur un service ci-contre pour afficher sa localisation sur la carte</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Services List (Right side) -->
          <div class="space-y-4">
            <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
              <h2 class="text-lg font-semibold text-slate-900 mb-4">Services & Localisation</h2>
              
              <div v-if="loading" class="text-center py-4">
                <p class="text-slate-600">⏳ Chargement des services...</p>
              </div>

              <div v-else class="space-y-3">
                <div v-for="service in services" :key="service.id"
                     @click="selectService(service)"
                     :class="['p-4 rounded-lg border-2 transition cursor-pointer', 
                              selectedService?.id === service.id 
                                ? 'bg-emerald-50 border-emerald-400' 
                                : 'bg-slate-50 border-slate-300 hover:border-emerald-300']">
                  <div class="flex items-start gap-3">
                    <span class="text-2xl flex-shrink-0">🏥</span>
                    <div class="flex-1">
                      <h3 class="font-semibold text-slate-900">{{ service.name }}</h3>
                      <p class="text-xs text-slate-600 mt-1">Code: {{ service.code }}</p>
                      <div v-if="service.location_lat && service.location_long" class="flex gap-2 mt-2">
                        <span class="text-xs bg-blue-100 text-blue-900 px-2 py-1 rounded">
                          📍 {{ service.location_lat }}, {{ service.location_long }}
                        </span>
                      </div>
                      <div v-else class="text-xs text-amber-600 mt-2">
                        ⚠️ Localisation non disponible
                      </div>
                      <p class="text-xs text-slate-500 mt-2">
                        24h/24: <span :class="service.is_open_h24 ? 'text-emerald-600 font-bold' : 'text-slate-600'">
                          {{ service.is_open_h24 ? '✓ Ouvert' : '✗ Horaires normaux' }}
                        </span>
                      </p>
                    </div>
                  </div>
                </div>

                <div v-if="services.length === 0" class="text-center py-8">
                  <p class="text-slate-600 text-sm">Aucun service trouvé</p>
                </div>
              </div>
            </div>

            <!-- Info Card -->
            <div v-if="selectedService" class="bg-emerald-50 border border-emerald-200 rounded-xl p-4">
              <h3 class="font-semibold text-emerald-900 mb-2">Service Sélectionné</h3>
              <div class="space-y-1 text-sm text-emerald-800">
                <p><strong>Nom:</strong> {{ selectedService.name }}</p>
                <p><strong>Bâtiment:</strong> {{ selectedService.building_name }}</p>
                <p><strong>Lits disponibles:</strong> {{ getTotalBedsCount(selectedService.id) }}</p>
                <button @click="openNavigation" class="mt-3 w-full bg-emerald-600 hover:bg-emerald-700 text-white py-2 rounded-lg text-sm font-medium transition">
                  📍 Ouvrir dans Maps
                </button>
              </div>
            </div>

            <!-- Help Box -->
            <div class="bg-blue-50 border border-blue-200 rounded-xl p-4 text-xs text-blue-800">
              <strong>💡 Aide à la navigation</strong><br><br>
              Cette vue permet aux visiteurs de localiser rapidement les services hospitaliers grâce aux coordonnées GPS. 
              Les services avec "24h/24" sont les urgences et laboratoires accessibles à tout moment.
            </div>
          </div>
        </div>

        <!-- Rooms & Beds Section -->
        <div v-if="selectedService" class="mt-8">
          <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
            <h2 class="text-lg font-semibold text-slate-900 mb-4">
              Chambres & Lits - {{ selectedService.name }}
            </h2>
            
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div v-for="room in getRoomsForService(selectedService.id)" :key="room.id"
                   class="border border-slate-200 rounded-lg p-4 hover:shadow-md transition">
                <div class="flex justify-between items-center mb-3">
                  <h3 class="font-semibold text-slate-900">Chambre {{ room.number }}</h3>
                  <span :class="['text-xs font-bold px-2 py-1 rounded',
                                  room.room_type === 'ICU' ? 'bg-red-100 text-red-700' :
                                  room.room_type === 'VIP' ? 'bg-purple-100 text-purple-700' :
                                  'bg-blue-100 text-blue-700']">
                    {{ room.room_type === 'ICU' ? 'Soins Intensifs' : room.room_type === 'VIP' ? 'VIP' : 'Standard' }}
                  </span>
                </div>
                <div class="space-y-2">
                  <div v-for="bed in getBeds(room.id)" :key="bed.id" class="flex items-center gap-2 text-sm">
                    <span :class="bed.is_occupied ? 'text-red-500' : 'text-emerald-500'">
                      {{ bed.is_occupied ? '✗ Occupé' : '✓ Libre' }}
                    </span>
                    <span class="text-slate-600">Lit {{ bed.number }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import AppLayout from '@/components/AppLayout.vue';
import api from '@/api';

const services = ref([]);
const rooms = ref([]);
const beds = ref([]);
const selectedService = ref(null);
const loading = ref(false);

const fetchServices = async () => {
  loading.value = true;
  try {
    const response = await api.instance.get('/clinical/services');
    const data = response.data;
    services.value = Array.isArray(data) ? data : (data?.services || []);
  } catch (error) {
    console.error('Erreur chargement services:', error);
    services.value = [];
  } finally {
    loading.value = false;
  }
};

const fetchRooms = async () => {
  try {
    const response = await api.instance.get('/clinical/rooms/');
    const data = response.data;
    rooms.value = Array.isArray(data) ? data : (data?.rooms || []);
  } catch (error) {
    console.error('Erreur chargement chambres:', error);
    rooms.value = [];
  }
};

const fetchBeds = async () => {
  try {
    const response = await api.instance.get('/clinical/beds/');
    const data = response.data;
    const list = Array.isArray(data) ? data : (data?.beds || []);
    beds.value = list.map((b) => ({
      ...b,
      room: b.room_id,
    }));
  } catch (error) {
    console.error('Erreur chargement lits:', error);
    beds.value = [];
  }
};

const getRoomsForService = (serviceId) => {
  return rooms.value.filter(r => r.service === serviceId);
};

const getBeds = (roomId) => {
  return beds.value.filter((b) => {
    const rid = b.room ?? b.room_id;
    return Number(rid) === Number(roomId);
  });
};

const getTotalBedsCount = (serviceId) => {
  let total = 0;
  const serviceRooms = getRoomsForService(serviceId);
  for (const room of serviceRooms) {
    total += getBeds(room.id).length;
  }
  return total;
};

const selectService = (service) => {
  selectedService.value = service;
};

const openNavigation = () => {
  if (selectedService.value?.location_lat && selectedService.value?.location_long) {
    // Ouvrir Google Maps avec les coordonnées
    const lat = selectedService.value.location_lat;
    const long = selectedService.value.location_long;
    const mapsUrl = `https://maps.google.com/?q=${lat},${long}`;
    window.open(mapsUrl, '_blank');
  } else {
    alert('Coordonnées GPS non disponibles pour ce service.');
  }
};

onMounted(() => {
  fetchServices();
  fetchRooms();
  fetchBeds();
});
</script>

<style scoped>
#map-container {
  min-height: 500px;
  width: 100%;
}

/* Support for future Leaflet integration */
@media (max-width: 1024px) {
  #map-container {
    min-height: 350px;
  }
}
</style>
