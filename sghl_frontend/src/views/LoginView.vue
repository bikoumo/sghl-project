<template>
  <div class="login-wrapper">
    <div class="login-card">
      <div class="login-header">
        <div class="hospital-logo">🏥</div>
        <h2>SGHL Portal</h2>
        <p>{{ showVerification ? 'Entrez le code reçu par email' : 'Système de Gestion Hospitalière Localisée' }}</p>
      </div>

      <div v-if="errorMessage" class="error-banner">{{ errorMessage }}</div>

      <form @submit.prevent="handleLogin" class="login-form">
        <div v-if="showVerification" class="input-group">
          <label for="code">Code de sécurité</label>
          <input type="text" id="code" v-model="verificationCode" placeholder="Ex: 123456" required />
        </div>

        <template v-else>
          <div class="input-group">
            <label for="email">Adresse Email</label>
            <input type="email" id="email" v-model="email" placeholder="nom@hopital.com" required />
          </div>
          <div class="input-group">
            <label for="password">Mot de passe</label>
            <input type="password" id="password" v-model="password" placeholder="••••••••" required />
          </div>
          <div class="input-group">
            <label for="role">Rôle</label>
            <select id="role" v-model="selectedRole">
              <option value="PATIENT">Patient</option>
              <option value="DOCTOR">Docteur</option>
              <option value="ADMIN">Admin</option>
              <option value="SECRETARY">Secrétaire</option>
              <option value="OTHER">Autre membre</option>
            </select>
          </div>
          <div v-if="selectedRole === 'DOCTOR'" class="input-group">
            <label for="service">Service</label>
            <input type="text" id="service" v-model="selectedService" placeholder="Ex: PEDIATRIE" />
          </div>
        </template>

        <button type="submit" class="btn-login" :disabled="loading">
          {{ loading ? 'En cours...' : (showVerification ? 'Valider le code' : 'Se connecter') }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import api from '@/api';

const email = ref('');
const password = ref('');
const verificationCode = ref('');
const selectedRole = ref('PATIENT');
const selectedService = ref('');
const showVerification = ref(false);
const errorMessage = ref('');
const loading = ref(false);
const router = useRouter();
const storedUsername = ref('');

const getDashboardRoute = (role) => {
  const normalizedRole = (role || '').toUpperCase();
  if (normalizedRole === 'DOCTOR') return '/dashboard/doctor';
  if (normalizedRole === 'PATIENT') return '/dashboard/patient';
  if (normalizedRole === 'ADMIN') return '/dashboard/admin';
  if (normalizedRole === 'SECRETARY' || normalizedRole === 'SECRETARY_GENERAL' || normalizedRole === 'SECRETARY_SERVICE') return '/dashboard/secretary';
  return '/dashboard';
};

const handleLogin = async () => {
  if (loading.value) return;
  loading.value = true;
  errorMessage.value = '';

  try {
    if (!showVerification.value) {
      await api.login({ username: email.value, password: password.value, role: selectedRole.value, service: selectedService.value });
      storedUsername.value = email.value;
      showVerification.value = true;
      loading.value = false;
    } else {
      const response = await api.verifyMfa({
        username: storedUsername.value,
        code: verificationCode.value,
      });
      const data = response.data || response;

      if (data.status === 'success') {
        const userPayload = { ...data, role: data.role || selectedRole.value, service: data.service || selectedService.value };
        if (data.token) localStorage.setItem('token', data.token);
        localStorage.setItem('user', JSON.stringify(userPayload));
        router.replace(getDashboardRoute(userPayload.role));
      } else {
        loading.value = false;
        errorMessage.value = data.message || 'Code incorrect.';
      }
    }
  } catch (error) {
    loading.value = false;
    errorMessage.value = error?.response?.data?.detail || error?.response?.data?.message || 'Erreur de connexion.';
  }
};
</script>

<style scoped>
/* Garde ton style CSS actuel ici */
.login-wrapper { display: flex; justify-content: center; align-items: center; min-height: 100vh; background: linear-gradient(135deg, #e0eafc, #cfdef3); padding: 20px; }
.login-card { background: #ffffff; padding: 40px; border-radius: 12px; box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1); width: 100%; max-width: 400px; }
.login-header { text-align: center; margin-bottom: 30px; }
.hospital-logo { font-size: 3rem; margin-bottom: 10px; }
.login-header h2 { margin: 0; color: #2c3e50; font-size: 1.8rem; }
.login-header p { color: #7f8c8d; margin: 5px 0 0 0; font-size: 0.9rem; }
.error-banner { background-color: #fde8e8; color: #e74c3c; padding: 10px; border-radius: 6px; margin-bottom: 20px; font-size: 0.9rem; text-align: center; border: 1px solid #f8b4b4; }
.login-form { display: flex; flex-direction: column; gap: 20px; }
.input-group { display: flex; flex-direction: column; gap: 8px; }
.input-group label { font-weight: 600; color: #34495e; font-size: 0.9rem; }
.input-group input { padding: 12px; border: 1px solid #dcdde1; border-radius: 6px; font-size: 1rem; }
.btn-login { background-color: #3498db; color: white; border: none; padding: 14px; border-radius: 6px; font-size: 1rem; font-weight: bold; cursor: pointer; transition: background-color 0.3s; }
.btn-login:hover { background-color: #2980b9; }
.btn-login:disabled { background-color: #bdc3c7; cursor: not-allowed; }
</style>