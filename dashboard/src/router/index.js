import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../components/MainLayout.vue'
import { isAuthenticated, getCurrentUser } from '../services/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginView.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: MainLayout,
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        redirect: '/sniffer'
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('../views/ProfileView.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'admin',
        name: 'AdminPanel',
        component: () => import('../views/AdminPanelView.vue'),
        meta: { requiresAuth: true, requiresAdmin: true }
      },
      {
        path: 'sniffer',
        name: 'Sniffer',
        component: () => import('../views/SnifferView.vue')
      },
      {
        path: 'system-info',
        name: 'SystemInfo',
        component: () => import('../views/SystemInfoView.vue')
      },
      {
        path: 'packet-processor',
        name: 'PacketProcessor',
        component: () => import('../views/PacketProcessorView.vue')
      },
      {
        path: 'ml-data-processor',
        name: 'MLDataProcessor',
        component: () => import('../views/MLDataProcessorView.vue')
      },
      {
        path: 'ml-training',
        name: 'MLTraining',
        component: () => import('../views/MLTrainingView.vue')
      },
      {
        path: 'threat-detection',
        name: 'ThreatDetection',
        component: () => import('../views/ThreatDetectionView.vue')
      },
      {
        path: 'statistics',
        name: 'Statistics',
        component: () => import('../views/StatisticsView.vue')
      },
      {
        path: 'notifications',
        name: 'Notifications',
        component: () => import('../views/NotificationsView.vue')
      },
      {
        path: 'about',
        name: 'About',
        component: () => import('../views/AboutView.vue')
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guard
router.beforeEach(async (to, from, next) => {
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth !== false)
  const requiresAdmin = to.matched.some(record => record.meta.requiresAdmin === true)
  
  if (requiresAuth && !isAuthenticated()) {
    next('/login')
  } else if (to.path === '/login' && isAuthenticated()) {
    next('/')
  } else if (requiresAdmin) {
    try {
      const user = await getCurrentUser()
      if (user.role !== 'admin') {
        next('/')
      } else {
        next()
      }
    } catch (error) {
      console.error('Failed to verify admin status:', error)
      next('/')
    }
  } else {
    next()
  }
})

export default router
