<template>
  <div class="main-layout">
    <div class="sidebar">
      <router-link to="/about" class="logo-container">
        <img src="../assets/logo.svg" alt="Hardbake Logo" class="logo">
        <span class="project-name">Hardbake</span>
      </router-link>
      <div class="service-tabs">
        <router-link
          v-for="service in services"
          :key="service.id"
          :to="service.path"
          class="tab"
          active-class="active"
        >
          {{ $t(`nav.${service.id}`) }}
        </router-link>
      </div>
      <div class="user-section">
        <router-link to="/profile" class="user-link">
          <i class="fas fa-user"></i>
          {{ $t('nav.profile') }}
        </router-link>
        <router-link v-if="isAdmin" to="/admin" class="user-link">
          ⚔ {{ $t('nav.admin') }}
        </router-link>
        <LanguageSwitcher />
      </div>
      <div class="logout-container">
        <button @click="handleLogout" class="logout-button">
          {{ $t('common.logout') }}
        </button>
      </div>
    </div>
    <div class="content">
      <router-view />
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { logout, getCurrentUser } from '../services/auth';
import LanguageSwitcher from './LanguageSwitcher.vue';

export default {
  name: 'MainLayout',
  components: {
    LanguageSwitcher
  },
  setup() {
    const router = useRouter();
    const { t } = useI18n();
    const isAdmin = ref(false);
    const services = [
      { id: 'sniffer', name: t('nav.sniffer'), path: '/sniffer' },
      { id: 'systemInfo', name: t('nav.systemInfo'), path: '/system-info' },
      { id: 'packetProcessor', name: t('nav.packetProcessor'), path: '/packet-processor' },
      { id: 'mlDataProcessor', name: t('nav.mlDataProcessor'), path: '/ml-data-processor' },
      { id: 'mlTraining', name: t('nav.mlTraining'), path: '/ml-training' },
      { id: 'threatDetection', name: t('nav.threatDetection'), path: '/threat-detection' },
      { id: 'notifications', name: t('nav.notifications'), path: '/notifications' },
      { id: 'statistics', name: t('nav.statistics'), path: '/statistics' },
      { id: 'about', name: t('nav.about'), path: '/about' }
    ];

    const handleLogout = async () => {
      try {
        await logout();
        router.push('/login');
      } catch (error) {
        console.error('Logout failed:', error);
      }
    };

    onMounted(async () => {
      try {
        const user = await getCurrentUser();
        isAdmin.value = user.role === 'admin';
      } catch (error) {
        console.error('Failed to get user role:', error);
      }
    });

    return {
      services,
      handleLogout,
      isAdmin
    };
  }
};
</script>

<style scoped>
.main-layout {
  display: flex;
  min-height: 100vh;
  width: 100%;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}

.sidebar {
  width: 250px;
  min-width: 250px;
  background-color: #2c3e50;
  padding: 20px 0;
  display: flex;
  flex-direction: column;
}

.logo-container {
  margin-top: -20px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 10px 0;
  text-decoration: none;
  color: white;
  transition: opacity 0.3s;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  width: 100%;
  box-sizing: border-box;
  position: relative;
}

.logo-container:hover {
  opacity: 0.8;
  background-color: rgba(255, 255, 255, 0.05);
}

.logo {
  width: 65px;
  height: 65px;
  margin-right: 0px;
  flex-shrink: 0;
}

.project-name {
  font-size: 1.6em;
  font-weight: bold;
  text-align: center;
  flex-shrink: 0;
  margin-top: 5px;
}

.service-tabs {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.tab {
  padding: 15px 20px;
  cursor: pointer;
  transition: background-color 0.3s;
  color: white;
  text-decoration: none;
  display: block;
}

.tab:hover {
  background-color: #34495e;
}

.tab.active {
  background-color: #3498db;
}

.content {
  flex: 1;
  padding: 20px;
  background-color: #f5f6fa;
  overflow-y: auto;
  min-width: 0;
}

.logout-container {
  padding: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.logout-button {
  width: 100%;
  padding: 12px;
  background-color: #e74c3c;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: background-color 0.3s;
}

.logout-button:hover {
  background-color: #c0392b;
}

.logout-button i {
  font-size: 1.1em;
}

.user-section {
  padding: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.user-link {
  color: white;
  text-decoration: none;
  padding: 10px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: background-color 0.3s;
}

.user-link:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.user-link i {
  width: 20px;
  text-align: center;
}
</style> 