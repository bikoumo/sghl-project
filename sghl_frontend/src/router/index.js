import { createRouter, createWebHistory } from 'vue-router'

const STAFF_ROLES = ['ADMIN', 'DOCTOR', 'SECRETARY']
const CLINICAL_ROLES = ['ADMIN', 'DOCTOR', 'SECRETARY']
const ADMIN_ONLY = ['ADMIN']

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'home', component: () => import('../views/HomeView.vue'), meta: { requiresAuth: false } },
    { path: '/login', name: 'login', component: () => import('../views/LoginView.vue'), meta: { requiresAuth: false } },
    {
      path: '/dashboard',
      name: 'dashboard',
      redirect: () => {
        try {
          const user = JSON.parse(localStorage.getItem('user') || '{}')
          const role = user.role
          const r = (role || '').toUpperCase()
          if (['DG', 'ADMIN'].includes(r)) return '/dashboard/admin'
          if (['DOCTOR', 'BIOLOGIST', 'OTHER'].includes(r)) return '/dashboard/doctor'
          if (['SECRETARY', 'SECRETARY_GENERAL', 'SECRETARY_SERVICE'].includes(r)) return '/dashboard/secretary'
          if (r === 'PATIENT') return '/dashboard/patient'
        } catch { /* ignore */ }
        return '/login'
      },
    },

    { path: '/dashboard/patient', name: 'dashboard-patient', component: () => import('../views/DashboardView.vue'), meta: { requiresAuth: true, role: 'PATIENT' } },
    { path: '/dashboard/doctor', name: 'dashboard-doctor', component: () => import('../views/DashboardView.vue'), meta: { requiresAuth: true, role: 'DOCTOR' } },
    { path: '/dashboard/admin', name: 'dashboard-admin', component: () => import('../views/DashboardView.vue'), meta: { requiresAuth: true, role: 'ADMIN' } },
    { path: '/dashboard/secretary', name: 'dashboard-secretary', component: () => import('../views/DashboardView.vue'), meta: { requiresAuth: true, role: 'SECRETARY' } },

    { path: '/patients', name: 'patients', component: () => import('../views/PatientDetailView.vue'), meta: { requiresAuth: true, role: CLINICAL_ROLES } },
    { path: '/patients/:id', name: 'patient-detail', component: () => import('../views/PatientDetailView.vue'), meta: { requiresAuth: true, role: CLINICAL_ROLES } },
    { path: '/laboratory', name: 'laboratory', component: () => import('../views/LaboratoryView.vue'), meta: { requiresAuth: true, role: CLINICAL_ROLES } },
    { path: '/pharmacy', name: 'pharmacy', component: () => import('../views/PharmacyView.vue'), meta: { requiresAuth: true, role: ['ADMIN', 'DOCTOR', 'SECRETARY'] } },
    { path: '/payments', name: 'payments', component: () => import('../views/PaymentsView.vue'), meta: { requiresAuth: true, role: ['ADMIN', 'DOCTOR', 'SECRETARY', 'PATIENT'] } },
    { path: '/visitors', name: 'visitors', component: () => import('../views/VisitorsMapView.vue'), meta: { requiresAuth: true, role: ['ADMIN', 'SECRETARY'] } },
    { path: '/pediatrie', name: 'pediatrie', component: () => import('../views/PediatrieView.vue'), meta: { requiresAuth: true, role: CLINICAL_ROLES } },
    { path: '/staff', name: 'staff', component: () => import('../views/StaffView.vue'), meta: { requiresAuth: true, role: ['ADMIN', 'SECRETARY'] } },

    { path: '/consultation', name: 'consultation', component: () => import('../views/ConsultationView.vue'), meta: { requiresAuth: true, role: CLINICAL_ROLES } },
    { path: '/appointments', name: 'appointments', component: () => import('../views/AppointmentsView.vue'), meta: { requiresAuth: true } },
    { path: '/beds', name: 'beds', component: () => import('../views/BedsView.vue'), meta: { requiresAuth: true, role: STAFF_ROLES } },
    { path: '/maternity', name: 'maternity', component: () => import('../views/MaternityView.vue'), meta: { requiresAuth: true, role: CLINICAL_ROLES } },
    { path: '/profile', name: 'profile', component: () => import('../views/ProfileView.vue'), meta: { requiresAuth: true } },
    { path: '/stats', name: 'stats', component: () => import('../views/StatsView.vue'), meta: { requiresAuth: true, role: STAFF_ROLES } },
    { path: '/about', name: 'about', component: () => import('../views/AboutView.vue'), meta: { requiresAuth: true } },
    { path: '/settings', name: 'settings', component: () => import('../views/SettingsView.vue'), meta: { requiresAuth: true, role: ADMIN_ONLY } },
    { path: '/chat', name: 'chat', component: () => import('../views/ChatView.vue'), meta: { requiresAuth: true, role: STAFF_ROLES } },
    { path: '/visit', name: 'visit', component: () => import('../views/VisitView.vue'), meta: { requiresAuth: true, role: ['ADMIN', 'DOCTOR', 'SECRETARY'] } },
  ],
})

function normalizeRole(role) {
  const r = (role || '').toUpperCase()
  if (['DG', 'ADMIN'].includes(r)) return 'ADMIN'
  if (['SECRETARY', 'SECRETARY_GENERAL', 'SECRETARY_SERVICE'].includes(r)) return 'SECRETARY'
  if (['DOCTOR', 'BIOLOGIST', 'OTHER'].includes(r)) return 'DOCTOR'
  if (r === 'PATIENT') return 'PATIENT'
  return null
}

function getRoleBasedDashboard(role) {
  const normalized = normalizeRole(role)
  if (normalized === 'DOCTOR') return '/dashboard/doctor'
  if (normalized === 'ADMIN') return '/dashboard/admin'
  if (normalized === 'SECRETARY') return '/dashboard/secretary'
  if (normalized === 'PATIENT') return '/dashboard/patient'
  return null
}

function clearSession() {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
}

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const storedUser = localStorage.getItem('user')
  let userRole = null

  try {
    userRole = storedUser ? JSON.parse(storedUser).role : null
  } catch {
    localStorage.removeItem('user')
  }

  const normalizedUser = normalizeRole(userRole)
  if (token && !normalizedUser) {
    clearSession()
  }

  const isAuthenticated = !!localStorage.getItem('token') && !!normalizeRole(
    (() => {
      try {
        return JSON.parse(localStorage.getItem('user') || '{}').role
      } catch {
        return null
      }
    })(),
  )

  if (to.name === 'login' && (to.query.force === '1' || to.query.logout === '1')) {
    clearSession()
    return next()
  }

  if (to.name === 'login' && isAuthenticated) {
    const dest = getRoleBasedDashboard(userRole)
    if (dest && dest !== '/login') {
      return next({ path: dest, replace: true })
    }
    clearSession()
    return next()
  }

  if (to.meta.requiresAuth && !isAuthenticated) {
    return next({ name: 'login', query: { redirect: to.fullPath } })
  }

  if (to.meta.role && isAuthenticated) {
    const allowed = Array.isArray(to.meta.role) ? to.meta.role : [to.meta.role]
    const normalizedAllowed = allowed.map((r) => normalizeRole(r))
    if (!normalizedAllowed.includes(normalizedUser)) {
      const dest = getRoleBasedDashboard(userRole) || '/login'
      return next({ path: dest, replace: true })
    }
  }

  next()
})

export default router
