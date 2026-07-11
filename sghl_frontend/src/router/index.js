import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('../views/HomeView.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      redirect: () => '/dashboard/patient'
    },
    {
      path: '/dashboard/patient',
      name: 'dashboard-patient',
      component: () => import('../views/DashboardView.vue'),
      meta: { requiresAuth: true, role: 'PATIENT' }
    },
    {
      path: '/dashboard/doctor',
      name: 'dashboard-doctor',
      component: () => import('../views/DashboardView.vue'),
      meta: { requiresAuth: true, role: 'DOCTOR' }
    },
    {
      path: '/dashboard/admin',
      name: 'dashboard-admin',
      component: () => import('../views/DashboardView.vue'),
      meta: { requiresAuth: true, role: 'ADMIN' }
    },
    {
      path: '/dashboard/secretary',
      name: 'dashboard-secretary',
      component: () => import('../views/DashboardView.vue'),
      meta: { requiresAuth: true, role: 'SECRETARY' }
    },
    {
      path: '/consultation',
      name: 'consultation',
      component: () => import('../views/ConsultationView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/appointments',
      name: 'appointments',
      component: () => import('../views/AppointmentsView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/beds',
      name: 'beds',
      component: () => import('../views/BedsView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/maternity',
      name: 'maternity',
      component: () => import('../views/MaternityView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('../views/ProfileView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/stats',
      name: 'stats',
      component: () => import('../views/StatsView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/about',
      name: 'about',
      component: () => import('../views/AboutView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/staff',
      name: 'staff',
      component: () => import('../views/StaffView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('../views/SettingsView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/chat',
      name: 'chat',
      component: () => import('../views/ChatView.vue'),
      meta: { requiresAuth: true }
    }
  ]
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
  return '/login'
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

  const isAuthenticated = !!token

  if (to.meta.requiresAuth && !isAuthenticated) {
    return next({ name: 'login', query: { redirect: to.fullPath } })
  }

  if (to.name === 'login' && isAuthenticated) {
    return next({ path: getRoleBasedDashboard(userRole), replace: true })
  }

  if (to.path === '/dashboard' && isAuthenticated) {
    return next({ path: getRoleBasedDashboard(userRole), replace: true })
  }

  if (to.meta.role && userRole) {
    const normalizedUser = normalizeRole(userRole)
    const normalizedRoute = normalizeRole(to.meta.role)
    if (normalizedUser && normalizedRoute && normalizedUser !== normalizedRoute) {
      return next({ path: getRoleBasedDashboard(userRole), replace: true })
    }
  }

  next()
})

export default router
