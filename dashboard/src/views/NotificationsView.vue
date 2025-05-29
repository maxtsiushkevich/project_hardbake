<template>
  <div class="notifications-container">
    <h1>{{ $t('notifications.title') }}</h1>
    
    <!-- Status and Controls Section -->
    <div class="status-section">
      <div class="status-card">
        <h2>{{ $t('notifications.consuming.title') }}</h2>
        <div class="controls">
          <div class="button-group">
            <button 
              @click="startConsuming" 
              :disabled="status === 'Running'"
            >
              {{ $t('notifications.consuming.start') }}
            </button>
            <button 
              @click="stopConsuming" 
              :disabled="status !== 'Running'"
            >
              {{ $t('notifications.consuming.stop') }}
            </button>
          </div>
        </div>
        <div class="status-indicator-row">
          <div class="status-indicator" :class="statusClass">
            {{ status }}
          </div>
          <button @click="loadStatus" class="refresh-button" :title="$t('common.refresh')">
            <span class="refresh-icon">↻</span>
          </button>
        </div>
        <div class="error-message" v-if="error">{{ error }}</div>
      </div>
    </div>

    <!-- Meta List Section -->
    <div class="meta-section">
      <h2>{{ $t('notifications.meta.title') }}</h2>
      
      <!-- Filters -->
      <div class="filters">
        <div class="filter-params">
          <div class="input-group">
            <label for="src_ip">{{ $t('notifications.meta.filters.srcIp') }}:</label>
            <input 
              id="src_ip"
              v-model="filters.src_ip" 
              :placeholder="$t('notifications.meta.filters.srcIp')" 
              @input="validateIp('src_ip')"
              :class="{ 'error': validationErrors.src_ip }"
            >
            <span class="error-message" v-if="validationErrors.src_ip">{{ validationErrors.src_ip }}</span>
          </div>

          <div class="input-group">
            <label for="dst_ip">{{ $t('notifications.meta.filters.dstIp') }}:</label>
            <input 
              id="dst_ip"
              v-model="filters.dst_ip" 
              :placeholder="$t('notifications.meta.filters.dstIp')" 
              @input="validateIp('dst_ip')"
              :class="{ 'error': validationErrors.dst_ip }"
            >
            <span class="error-message" v-if="validationErrors.dst_ip">{{ validationErrors.dst_ip }}</span>
          </div>

          <div class="input-group">
            <label for="src_port">{{ $t('notifications.meta.filters.srcPort') }}:</label>
            <input 
              id="src_port"
              v-model.number="filters.src_port" 
              type="number" 
              :placeholder="$t('notifications.meta.filters.srcPort')"
              min="0"
              max="65535"
              @input="validatePort('src_port')"
              :class="{ 'error': validationErrors.src_port }"
            >
            <span class="error-message" v-if="validationErrors.src_port">{{ validationErrors.src_port }}</span>
          </div>

          <div class="input-group">
            <label for="dst_port">{{ $t('notifications.meta.filters.dstPort') }}:</label>
            <input 
              id="dst_port"
              v-model.number="filters.dst_port" 
              type="number" 
              :placeholder="$t('notifications.meta.filters.dstPort')"
              min="0"
              max="65535"
              @input="validatePort('dst_port')"
              :class="{ 'error': validationErrors.dst_port }"
            >
            <span class="error-message" v-if="validationErrors.dst_port">{{ validationErrors.dst_port }}</span>
          </div>

          <div class="input-group">
            <label for="proto">{{ $t('notifications.meta.filters.protocol') }}:</label>
            <input 
              id="proto"
              v-model.number="filters.proto" 
              type="number" 
              :placeholder="$t('notifications.meta.filters.protocol')"
            >
          </div>

          <div class="input-group">
            <label for="start_time">{{ $t('notifications.meta.filters.startTime') }}:</label>
            <input 
              id="start_time"
              v-model="filters.start_time" 
              type="datetime-local" 
              :min="filters.end_time || undefined"
              step="1"
            >
          </div>

          <div class="input-group">
            <label for="end_time">{{ $t('notifications.meta.filters.endTime') }}:</label>
            <input 
              id="end_time"
              v-model="filters.end_time" 
              type="datetime-local" 
              :max="filters.start_time || undefined"
              step="1"
            >
          </div>

          <div class="input-group">
            <label for="min_duration">{{ $t('notifications.meta.filters.minDuration') }}:</label>
            <input 
              id="min_duration"
              v-model.number="filters.min_duration" 
              type="number" 
              :placeholder="$t('notifications.meta.filters.minDuration')"
            >
          </div>

          <div class="input-group">
            <label for="max_duration">{{ $t('notifications.meta.filters.maxDuration') }}:</label>
            <input 
              id="max_duration"
              v-model.number="filters.max_duration" 
              type="number" 
              :placeholder="$t('notifications.meta.filters.maxDuration')"
            >
          </div>
        </div>
        <button @click="loadMetaList">{{ $t('notifications.meta.filters.apply') }}</button>
        <button @click="clearFilters" class="btn btn-secondary" style="margin-left: 8px;">{{ $t('notifications.meta.filters.clear') }}</button>
      </div>

      <!-- Meta Table -->
      <div style="display: flex; justify-content: flex-end; align-items: center; margin-bottom: 8px;">
        <button class="refresh-button" @click="loadMetaList" :title="$t('common.refresh')">
          <span class="refresh-icon">↻</span>
        </button>
      </div>
      <div class="table-responsive">
        <table class="table">
          <thead>
            <tr>
              <th @click="sortMeta('id')">
                {{ $t('notifications.meta.table.id') }}
                <span v-if="filters.sort_by === 'id'">{{ filters.sort_order === 'asc' ? '▲' : '▼' }}</span>
              </th>
              <th @click="sortMeta('src_ip')">
                {{ $t('notifications.meta.table.srcIp') }}
                <span v-if="filters.sort_by === 'src_ip'">{{ filters.sort_order === 'asc' ? '▲' : '▼' }}</span>
              </th>
              <th @click="sortMeta('dst_ip')">
                {{ $t('notifications.meta.table.dstIp') }}
                <span v-if="filters.sort_by === 'dst_ip'">{{ filters.sort_order === 'asc' ? '▲' : '▼' }}</span>
              </th>
              <th @click="sortMeta('src_port')">
                {{ $t('notifications.meta.table.srcPort') }}
                <span v-if="filters.sort_by === 'src_port'">{{ filters.sort_order === 'asc' ? '▲' : '▼' }}</span>
              </th>
              <th @click="sortMeta('dst_port')">
                {{ $t('notifications.meta.table.dstPort') }}
                <span v-if="filters.sort_by === 'dst_port'">{{ filters.sort_order === 'asc' ? '▲' : '▼' }}</span>
              </th>
              <th @click="sortMeta('proto')">
                {{ $t('notifications.meta.table.protocol') }}
                <span v-if="filters.sort_by === 'proto'">{{ filters.sort_order === 'asc' ? '▲' : '▼' }}</span>
              </th>
              <th @click="sortMeta('timestamp')">
                {{ $t('notifications.meta.table.timestamp') }}
                <span v-if="filters.sort_by === 'timestamp'">{{ filters.sort_order === 'asc' ? '▲' : '▼' }}</span>
              </th>
              <th @click="sortMeta('duration')">
                {{ $t('notifications.meta.table.duration') }}
                <span v-if="filters.sort_by === 'duration'">{{ filters.sort_order === 'asc' ? '▲' : '▼' }}</span>
              </th>
              <th>{{ $t('notifications.meta.table.actions') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in metaList.items" :key="item.id">
              <td>{{ item.id }}</td>
              <td>{{ item.src_ip }}</td>
              <td>{{ item.dst_ip }}</td>
              <td>{{ item.src_port }}</td>
              <td>{{ item.dst_port }}</td>
              <td>{{ item.proto }}</td>
              <td>{{ formatDate(item.timestamp) }}</td>
              <td>{{ item.duration }}</td>
              <td>
                <button @click="viewMetaDetails(item.id)" class="btn-sm">
                  {{ $t('notifications.meta.table.viewDetails') }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div class="pagination">
        <button 
          @click="changePage(metaList.page - 1)" 
          :disabled="metaList.page <= 1"
          class="pagination-button"
        >
          {{ $t('notifications.meta.pagination.previous') }}
        </button>
        <span>{{ $t('notifications.meta.pagination.page') }} {{ metaList.page }} {{ $t('notifications.meta.pagination.of') }} {{ metaList.total_pages }}</span>
        <button 
          @click="changePage(metaList.page + 1)" 
          :disabled="metaList.page >= metaList.total_pages"
          class="pagination-button"
        >
          {{ $t('notifications.meta.pagination.next') }}
        </button>
      </div>
    </div>

    <!-- Meta Details Modal -->
    <div v-if="showModal" class="modal">
      <div class="modal-content" ref="modalRef">
        <h3>{{ $t('notifications.meta.details.title') }}</h3>
        <div class="features-container">
          <div v-for="(value, key) in selectedMeta?.features" :key="key" class="feature-item">
            <span class="feature-key">{{ key }}:</span>
            <span class="feature-value">{{ value }}</span>
          </div>
        </div>
        <button @click="showModal = false" class="btn btn-secondary">{{ $t('notifications.meta.details.close') }}</button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { notificationService } from '@/services/notificationService';

export default {
  name: 'NotificationsView',
  setup() {
    const status = ref('Not running');
    const error = ref(null);
    const metaList = ref({
      items: [],
      total: 0,
      page: 1,
      page_size: 10,
      total_pages: 1
    });
    const filters = ref({
      src_ip: '',
      dst_ip: '',
      src_port: null,
      dst_port: null,
      proto: null,
      start_time: '',
      end_time: '',
      min_duration: null,
      max_duration: null,
      sort_by: 'timestamp',
      sort_order: 'desc'
    });
    const validationErrors = ref({});
    const showModal = ref(false);
    const selectedMeta = ref(null);
    const modalRef = ref(null);

    const handleClickOutside = (event) => {
      if (showModal.value && modalRef.value && !modalRef.value.contains(event.target)) {
        showModal.value = false;
      }
    };

    const loadStatus = async () => {
      try {
        const response = await notificationService.getStatus();
        status.value = response.status;
        error.value = response.error;
      } catch (err) {
        if (err.name === 'ValidationError') {
          error.value = err.errors.map(e => `${e.loc.join('.')}: ${e.msg}`).join('\n');
        } else {
          error.value = err.message;
        }
      }
    };

    const startConsuming = async () => {
      try {
        await notificationService.startConsuming();
        await loadStatus();
      } catch (err) {
        if (err.name === 'ValidationError') {
          error.value = err.errors.map(e => `${e.loc.join('.')}: ${e.msg}`).join('\n');
        } else {
          error.value = err.message;
        }
      }
    };

    const stopConsuming = async () => {
      try {
        await notificationService.stopConsuming();
        await loadStatus();
      } catch (err) {
        if (err.name === 'ValidationError') {
          error.value = err.errors.map(e => `${e.loc.join('.')}: ${e.msg}`).join('\n');
        } else {
          error.value = err.message;
        }
      }
    };

    const formatDateTimeForInput = (date) => {
      if (!date) return '';
      const d = new Date(date);
      return d.toISOString().slice(0, 16); // Format: YYYY-MM-DDTHH:mm
    };

    const formatDateTimeForAPI = (dateString) => {
      if (!dateString) return null;
      return new Date(dateString).toISOString();
    };

    const loadMetaList = async () => {
      try {
        // Format datetime values for API
        const apiParams = {
          ...filters.value,
          start_time: formatDateTimeForAPI(filters.value.start_time),
          end_time: formatDateTimeForAPI(filters.value.end_time),
          page: metaList.value.page,
          page_size: metaList.value.page_size
        };

        // Remove null values
        Object.keys(apiParams).forEach(key => {
          if (apiParams[key] === null || apiParams[key] === '') {
            delete apiParams[key];
          }
        });

        const response = await notificationService.getMetaList(apiParams);
        metaList.value = response;
        error.value = null;
      } catch (err) {
        if (err.name === 'ValidationError') {
          error.value = err.errors.map(e => `${e.loc.join('.')}: ${e.msg}`).join('\n');
        } else {
          error.value = err.message;
        }
      }
    };

    const changePage = (newPage) => {
      metaList.value.page = newPage;
      loadMetaList();
    };

    const viewMetaDetails = async (metaId) => {
      try {
        const response = await notificationService.getMetaWithFeatures(metaId);
        // Extract only the features part and format it
        selectedMeta.value = {
          id: response.id,
          features: formatFeatures(response.features)
        };
        showModal.value = true;
        error.value = null;
      } catch (err) {
        if (err.name === 'ValidationError') {
          error.value = err.errors.map(e => `${e.loc.join('.')}: ${e.msg}`).join('\n');
        } else {
          error.value = err.message;
        }
      }
    };

    const formatFeatures = (features) => {
      if (!features) return {};
      
      const formattedFeatures = {};
      for (const [key, value] of Object.entries(features)) {
        // Format the key to be more readable
        const formattedKey = key
          .replace(/_/g, ' ')
          .replace(/\b\w/g, l => l.toUpperCase());
        
        // Format the value based on its type
        let formattedValue = value;
        if (typeof value === 'number') {
          // Round to 4 decimal places if it's a float
          formattedValue = Number.isInteger(value) ? value : value.toFixed(4);
        } else if (typeof value === 'boolean') {
          formattedValue = value ? 'Yes' : 'No';
        } else if (Array.isArray(value)) {
          formattedValue = value.join(', ');
        }
        
        formattedFeatures[formattedKey] = formattedValue;
      }
      return formattedFeatures;
    };

    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleString();
    };

    const validateIp = (field) => {
      const value = filters.value[field];
      if (!value) {
        validationErrors.value[field] = '';
        return;
      }

      // IPv4 regex pattern
      const ipv4Pattern = /^(\d{1,3}\.){3}\d{1,3}$/;
      // IPv6 regex pattern
      const ipv6Pattern = /^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$/;

      if (!ipv4Pattern.test(value) && !ipv6Pattern.test(value)) {
        validationErrors.value[field] = 'Invalid IP address format';
        return;
      }

      if (ipv4Pattern.test(value)) {
        const parts = value.split('.');
        const isValid = parts.every(part => {
          const num = parseInt(part, 10);
          return num >= 0 && num <= 255;
        });

        if (!isValid) {
          validationErrors.value[field] = 'Invalid IPv4 address';
          return;
        }
      }

      validationErrors.value[field] = '';
    };

    const validatePort = (field) => {
      const value = filters.value[field];
      if (value === null || value === '') {
        validationErrors.value[field] = '';
        return;
      }

      if (!Number.isInteger(value) || value < 0 || value > 65535) {
        validationErrors.value[field] = 'Port must be between 0 and 65535';
        return;
      }

      validationErrors.value[field] = '';
    };

    const hasValidationErrors = computed(() => {
      return Object.values(validationErrors.value).some(error => error !== '');
    });

    const sortMeta = (column) => {
      if (filters.value.sort_by === column) {
        filters.value.sort_order = filters.value.sort_order === 'asc' ? 'desc' : 'asc';
      } else {
        filters.value.sort_by = column;
        filters.value.sort_order = 'desc';
      }
      loadMetaList();
    };

    const clearFilters = () => {
      filters.value = {
        src_ip: '',
        dst_ip: '',
        src_port: null,
        dst_port: null,
        proto: null,
        start_time: '',
        end_time: '',
        min_duration: null,
        max_duration: null,
        sort_by: 'timestamp',
        sort_order: 'desc'
      };
      validationErrors.value = {};
      loadMetaList();
    };

    onMounted(() => {
      loadStatus();
      loadMetaList();
      // Add click outside listener
      document.addEventListener('click', handleClickOutside);
    });

    onUnmounted(() => {
      // Remove click outside listener
      document.removeEventListener('click', handleClickOutside);
    });

    return {
      status,
      error,
      metaList,
      filters,
      showModal,
      selectedMeta,
      modalRef,
      validationErrors,
      hasValidationErrors,
      validateIp,
      validatePort,
      startConsuming,
      stopConsuming,
      loadMetaList,
      changePage,
      viewMetaDetails,
      formatDate,
      formatDateTimeForInput,
      loadStatus,
      sortMeta,
      clearFilters
    };
  },
  computed: {
    statusClass() {
      return {
        'status-running': this.status === 'Running',
        'status-stopped': this.status === 'Stopped',
        'status-error': this.status === 'Error',
        'status-not-running': this.status === 'Not running'
      };
    }
  }
};
</script>

<style scoped>
.notifications-container {
  padding: 20px;
}

.status-section {
  margin-bottom: 30px;
}

.status-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.status-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.refresh-button {
  padding: 5px 10px;
  background-color: #2ecc71;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.refresh-button:hover {
  background-color: #27ae60;
}

.refresh-icon {
  font-size: 1.2em;
  transition: transform 0.3s;
}

.refresh-button:hover .refresh-icon {
  transform: rotate(180deg);
}

.status-indicator {
  display: inline-block;
  padding: 8px 16px;
  border-radius: 4px;
  margin: 10px 0;
  font-weight: bold;
}

.status-running {
  background-color: #28a745;
  color: white;
}

.status-stopped {
  background-color: #dc3545;
  color: white;
}

.status-error {
  background-color: #ffc107;
  color: black;
}

.status-not-running {
  background-color: #6c757d;
  color: white;
}

.controls {
  margin-top: 15px;
}

.button-group {
  display: flex;
  gap: 10px;
  margin: 15px 0;
}

button {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  background-color: #3498db;
  color: white;
  cursor: pointer;
  transition: background-color 0.3s;
}

button:hover {
  background-color: #2980b9;
}

button:disabled {
  background-color: #95a5a6;
  cursor: not-allowed;
}

.filters {
  margin-bottom: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
}

.filter-params {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
  margin-bottom: 20px;
}

.input-group {
  display: flex;
  flex-direction: column;
}

.input-group label {
  margin-bottom: 5px;
  font-weight: bold;
}

.input-group input {
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  width: 100%;
}

.input-group input.error {
  border-color: #e74c3c;
}

.error-message {
  color: #e74c3c;
  font-size: 0.8em;
  margin-top: 4px;
  background: none !important;
  border: none !important;
  padding: 0 !important;
}

.table {
  width: 100%;
  margin-bottom: 20px;
  background: white;
  border-radius: 8px;
  overflow: hidden;
}

.table th,
.table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #dee2e6;
}

.table th {
  background-color: #f8f9fa;
  font-weight: bold;
  cursor: pointer;
  user-select: none;
}

.table th:last-child {
  cursor: default;
}

.table th span {
  margin-left: 4px;
  font-size: 0.9em;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 15px;
  margin-top: 20px;
}

.modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  padding: 20px;
  border-radius: 8px;
  max-width: 80%;
  max-height: 80vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  position: relative;
  z-index: 1001;
}

.modal-content h3 {
  margin: 0 0 20px 0;
  color: #2c3e50;
  border-bottom: 2px solid #e9ecef;
  padding-bottom: 10px;
}

.error-message {
  color: #dc3545;
  margin: 10px 0;
  white-space: pre-line;
  background-color: #f8d7da;
  border: 1px solid #f5c6cb;
  border-radius: 4px;
  padding: 10px;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
}

.btn-primary {
  background-color: #007bff;
  color: white;
}

.btn-danger {
  background-color: #dc3545;
  color: white;
}

.btn-secondary {
  background-color: #6c757d;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 8px 16px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.btn-secondary:hover {
  background-color: #c0392b;
  color: white;
}

.btn-info {
  background-color: #17a2b8;
  color: white;
}

.btn:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.btn-sm {
  padding: 4px 8px;
  font-size: 0.875rem;
}

.form-control[type="datetime-local"] {
  min-width: 200px;
}

.features-container {
  margin: 20px 0;
  max-height: 60vh;
  overflow-y: auto;
  background: #f8f9fa;
  border-radius: 4px;
  padding: 15px;
}

.feature-item {
  display: flex;
  padding: 8px;
  border-bottom: 1px solid #dee2e6;
}

.feature-item:last-child {
  border-bottom: none;
}

.feature-key {
  font-weight: bold;
  min-width: 200px;
  color: #495057;
}

.feature-value {
  flex: 1;
  color: #212529;
  word-break: break-word;
}

.error {
  border-color: #dc3545 !important;
}

.error-message {
  color: #dc3545;
  font-size: 0.875rem;
  margin-top: 0.25rem;
  display: block;
}

.status-indicator-row {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 10px;
  margin: 10px 0;
}

.pagination-button {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
  background-color: #3498db;
  color: white;
  transition: background-color 0.3s;
}

.pagination-button:hover:not(:disabled) {
  background-color: #2980b9;
}

.pagination-button:disabled {
  background-color: #95a5a6;
  color: white;
  cursor: not-allowed;
  opacity: 1;
}
</style> 