<template>
  <nav v-if="isLoggedIn" class="navbar">
    <router-link to="/dashboard">Tableau de Bord</router-link>
    <router-link to="/consultation">Consultation</router-link>
    <router-link to="/appointments">Rendez-vous</router-link>
    <router-link to="/beds">Lits</router-link>
    <router-link to="/stats">Statistiques</router-link>
    <router-link to="/staff">Personnel</router-link>
    <router-link to="/settings">Paramètres</router-link>
    <router-link to="/profile">Profil</router-link>
    <button @click="logout" class="btn-logout">Déconnexion</button>
  </nav>
  <router-view />
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
// Vérifie si un token existe pour afficher le menu
const isLoggedIn = computed(() => !!localStorage.getItem('token'))

const logout = () => {
  localStorage.removeItem('token')
  router.push('/')
}
</script>

<style>
.navbar { 
  padding: 15px; 
  background: #2c3e50; 
  display: flex; 
  gap: 20px; 
  align-items: center; 
}
.navbar a { 
  color: white; 
  text-decoration: none; 
  font-weight: bold; 
}
.btn-logout { 
  margin-left: auto; 
  background: #e74c3c; 
  color: white; 
  border: none; 
  padding: 8px 12px; 
  cursor: pointer; 
}
</style>