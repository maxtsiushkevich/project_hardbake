<template>
  <div class="admin-panel">
    <h1>{{ $t('admin.title') }}</h1>
    
    <!-- Create User Form -->
    <div class="section">
      <h2>{{ $t('admin.createUser.title') }}</h2>
      <form @submit.prevent="createUser" class="create-user-form">
        <div class="form-group">
          <label for="username">{{ $t('admin.createUser.username') }}:</label>
          <input 
            id="username"
            v-model="newUser.username"
            type="text"
            required
          >
        </div>
        
        <div class="form-group">
          <label for="password">{{ $t('admin.createUser.password') }}:</label>
          <input 
            id="password"
            v-model="newUser.password"
            type="password"
            required
          >
        </div>
        
        <div class="form-group">
          <label for="role">{{ $t('admin.createUser.role') }}:</label>
          <select id="role" v-model="newUser.role" required>
            <option value="admin">{{ $t('admin.createUser.roles.admin') }}</option>
            <option value="user">{{ $t('admin.createUser.roles.user') }}</option>
            <option value="viewer">{{ $t('admin.createUser.roles.viewer') }}</option>
          </select>
        </div>
        
        <button type="submit" class="btn-primary">{{ $t('admin.createUser.submit') }}</button>
      </form>
    </div>

    <!-- Users List -->
    <div class="section">
      <h2>{{ $t('admin.users.title') }}</h2>
      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>{{ $t('admin.users.table.username') }}</th>
              <th>{{ $t('admin.users.table.role') }}</th>
              <th>{{ $t('admin.users.table.status') }}</th>
              <th>{{ $t('admin.users.table.actions') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in users" :key="user.id">
              <td>{{ user.username }}</td>
              <td>{{ user.role }}</td>
              <td>
                <span :class="{ 'active': user.is_active }">
                  {{ user.is_active ? $t('admin.users.status.active') : $t('admin.users.status.inactive') }}
                </span>
              </td>
              <td>
                <button 
                  @click="deleteUser(user.username)"
                  class="btn-danger"
                  :disabled="user.username === currentUser?.username"
                >
                  {{ $t('admin.users.actions.delete') }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { authApi } from '../services/api'
import { getCurrentUser } from '../services/auth'

const { t } = useI18n()
const users = ref([])
const currentUser = ref(null)
const newUser = ref({
  username: '',
  password: '',
  role: 'user'
})

const loadUsers = async () => {
  try {
    const response = await authApi.get('/auth/users/')
    users.value = response.data
  } catch (error) {
    console.error('Failed to load users:', error)
  }
}

const createUser = async () => {
  try {
    await authApi.post('/auth/users/', newUser.value)
    await loadUsers()
    newUser.value = {
      username: '',
      password: '',
      role: 'user'
    }
  } catch (error) {
    console.error('Failed to create user:', error)
  }
}

const deleteUser = async (username) => {
  if (!confirm(t('admin.users.actions.deleteConfirm', { username }))) {
    return
  }
  
  try {
    await authApi.delete(`/auth/users/${username}`)
    await loadUsers()
  } catch (error) {
    console.error('Failed to delete user:', error)
  }
}

onMounted(async () => {
  currentUser.value = await getCurrentUser()
  await loadUsers()
})
</script>

<style scoped>
.admin-panel {
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

.section {
  background: white;
  border-radius: 8px;
  padding: 2rem;
  margin-bottom: 2rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.create-user-form {
  max-width: 500px;
  margin: 0 auto;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: bold;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.table-container {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 1rem;
}

th, td {
  padding: 0.75rem;
  text-align: left;
  border-bottom: 1px solid #ddd;
}

th {
  background-color: #f8f9fa;
  font-weight: bold;
}

.btn-primary {
  background-color: #007bff;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  width: 100%;
  margin-top: 1rem;
}

.btn-danger {
  background-color: #dc3545;
  color: white;
  border: none;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  cursor: pointer;
}

.btn-danger:disabled {
  background-color: #6c757d;
  cursor: not-allowed;
}

.active {
  color: #4CAF50;
  font-weight: bold;
}
</style> 