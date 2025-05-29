<template>
  <div class="profile-container">
    <h1>{{ $t('profile.title') }}</h1>
    <div v-if="user" class="profile-content">
      <div class="profile-info">
        <h2>{{ $t('profile.userInfo.title') }}</h2>
        <div class="info-item">
          <label>{{ $t('profile.userInfo.username') }}:</label>
          <span>{{ user.username }}</span>
        </div>
        <div class="info-item">
          <label>{{ $t('profile.userInfo.role') }}:</label>
          <span>{{ user.role }}</span>
        </div>
        <div class="info-item">
          <label>{{ $t('profile.userInfo.status') }}:</label>
          <span :class="{ 'active': user.is_active }">
            {{ user.is_active ? $t('profile.userInfo.active') : $t('profile.userInfo.inactive') }}
          </span>
        </div>
      </div>
    </div>
    <div v-else class="loading">
      {{ $t('profile.loading') }}
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getCurrentUser } from '../services/auth'

const user = ref(null)

onMounted(async () => {
  try {
    user.value = await getCurrentUser()
  } catch (error) {
    console.error('Failed to load user profile:', error)
  }
})
</script>

<style scoped>
.profile-container {
  padding: 2rem;
  max-width: 800px;
  margin: 0 auto;
}

.profile-content {
  background: white;
  border-radius: 8px;
  padding: 2rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  min-height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.profile-info {
  width: 100%;
  max-width: 500px;
}

.info-item {
  display: flex;
  margin-bottom: 1rem;
  padding: 0.75rem 0;
  border-bottom: 1px solid #eee;
  align-items: center;
}

.info-item:last-child {
  border-bottom: none;
  margin-bottom: 0;
}

.info-item label {
  font-weight: bold;
  width: 120px;
  color: #666;
  margin: 0;
}

.info-item span {
  flex: 1;
  margin: 0;
}

.active {
  color: #4CAF50;
  font-weight: bold;
}

.loading {
  text-align: center;
  padding: 2rem;
  color: #666;
}
</style> 