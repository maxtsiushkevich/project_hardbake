<template>
  <div class="sniffer-view">
    <h2>{{ $t('sniffer.title') }}</h2>
    
    <div class="control-panel">
      <div class="form-group">
        <div class="input-group">
          <label for="interface">{{ $t('sniffer.interface.label') }}:</label>
          <select id="interface" v-model="selectedInterface">
            <option value="">{{ $t('sniffer.interface.select') }}</option>
            <option v-for="iface in interfaces" :key="iface" :value="iface">
              {{ iface }}
            </option>
          </select>
        </div>
      </div>

      <div class="form-group">
        <div class="checkbox-group">
          <input type="checkbox" id="writeToFile" v-model="writeToFile" class="custom-checkbox">
          <label for="writeToFile" class="checkbox-label">{{ $t('sniffer.writeToFile') }}</label>
        </div>
      </div>

      <div class="form-group">
        <h3>{{ $t('sniffer.filterParams.title') }}</h3>
        <div class="filter-params">
          <div class="input-group">
            <label for="src_ip">{{ $t('sniffer.filterParams.srcIp') }}:</label>
            <input 
              id="src_ip"
              v-model="filter.src_ip" 
              :placeholder="$t('sniffer.filterParams.srcIp')"
              @input="validateIp('src_ip')"
              :class="{ 'error': validationErrors.src_ip }"
            >
            <span class="error-message" v-if="validationErrors.src_ip">{{ $t('sniffer.validation.invalidIp') }}</span>
          </div>

          <div class="input-group">
            <label for="dst_ip">{{ $t('sniffer.filterParams.dstIp') }}:</label>
            <input 
              id="dst_ip"
              v-model="filter.dst_ip" 
              :placeholder="$t('sniffer.filterParams.dstIp')"
              @input="validateIp('dst_ip')"
              :class="{ 'error': validationErrors.dst_ip }"
            >
            <span class="error-message" v-if="validationErrors.dst_ip">{{ $t('sniffer.validation.invalidIp') }}</span>
          </div>

          <div class="input-group">
            <label for="protocol">{{ $t('sniffer.filterParams.protocol') }}:</label>
            <select id="protocol" v-model="filter.protocol">
              <option value="">{{ $t('sniffer.filterParams.anyProtocol') }}</option>
              <option v-for="protocol in protocols" :key="protocol" :value="protocol">
                {{ protocol.toUpperCase() }}
              </option>
            </select>
          </div>

          <div class="input-group">
            <label for="src_port">{{ $t('sniffer.filterParams.srcPort') }}:</label>
            <input 
              id="src_port"
              v-model.number="filter.src_port" 
              type="number" 
              :placeholder="$t('sniffer.filterParams.srcPort')"
              min="0"
              max="65535"
              @input="validatePort('src_port')"
              :class="{ 'error': validationErrors.src_port }"
            >
            <span class="error-message" v-if="validationErrors.src_port">{{ validationErrors.src_port }}</span>
          </div>

          <div class="input-group">
            <label for="dst_port">{{ $t('sniffer.filterParams.dstPort') }}:</label>
            <input 
              id="dst_port"
              v-model.number="filter.dst_port" 
              type="number" 
              :placeholder="$t('sniffer.filterParams.dstPort')"
              min="0"
              max="65535"
              @input="validatePort('dst_port')"
              :class="{ 'error': validationErrors.dst_port }"
            >
            <span class="error-message" v-if="validationErrors.dst_port">{{ validationErrors.dst_port }}</span>
          </div>
        </div>
      </div>

      <div class="button-group">
        <button @click="startSniffing" :disabled="hasValidationErrors || !selectedInterface">{{ $t('sniffer.buttons.start') }}</button>
        <button @click="stopSniffing" :disabled="!isSniffing">{{ $t('sniffer.buttons.stop') }}</button>
      </div>
    </div>

    <div class="status-panel">
      <div class="status-header">
        <h3>{{ $t('sniffer.sessions.title') }}</h3>
        <div class="header-controls">
          <div class="status-filter">
            <label for="statusFilter">{{ $t('sniffer.sessions.filterByStatus') }}:</label>
            <select 
              id="statusFilter" 
              v-model="selectedStatus" 
              @change="handleStatusChange"
            >
              <option value="">{{ $t('sniffer.sessions.allStatuses') }}</option>
              <option value="Running">{{ $t('sniffer.sessions.running') }}</option>
              <option value="Stopped">{{ $t('sniffer.sessions.stopped') }}</option>
              <option value="Crashed">{{ $t('sniffer.sessions.crashed') }}</option>
            </select>
          </div>
          <div class="header-buttons">
            <button class="clear-button" @click="clearCache">
              ⌫ {{ $t('sniffer.buttons.clear') }}
            </button>
            <button class="refresh-button" @click="refreshData">
              <span class="refresh-icon">↻</span> {{ $t('sniffer.buttons.refresh') }}
            </button>
          </div>
        </div>
      </div>
      <div v-if="activeSessions.length === 0" class="no-sessions">
        {{ $t('sniffer.sessions.noSessions') }}
      </div>
      <div v-else class="sessions-list">
        <div v-for="session in currentPageItems" :key="session.sniff_id" class="session-card">
          <div class="session-info">
            <div>{{ $t('sniffer.sessions.interface') }}: {{ session.interface }}</div>
            <div>{{ $t('sniffer.sessions.started') }}: {{ formatDate(session.start_at) }}</div>
            <div v-if="session.stop_at">
              <div>{{ $t('sniffer.sessions.ended') }}: {{ formatDate(session.stop_at) }}</div>
              <div>{{ $t('sniffer.sessions.duration') }}: {{ calculateDuration(session.start_at, session.stop_at) }}</div>
            </div>
            <div>{{ $t('sniffer.sessions.status') }}: <span :class="{ 'status-running': session.status === 'Running', 'status-stopped': session.status !== 'Running' }">{{ $t(`sniffer.sessions.${session.status.toLowerCase()}`) }}</span></div>
          </div>
          <button @click="stopSession(session.sniff_id)">{{ $t('sniffer.buttons.stop') }}</button>
        </div>
      </div>
      <div v-if="activeSessions.length > 0" class="pagination-controls">
        <button 
          @click="previousPage" 
          :disabled="currentPage === 1"
          class="pagination-button"
        >
          {{ $t('sniffer.pagination.previous') }}
        </button>
        <span class="page-info">{{ $t('sniffer.pagination.page') }} {{ currentPage }} {{ $t('sniffer.pagination.of') }} {{ totalPages }}</span>
        <button 
          @click="nextPage" 
          :disabled="currentPage === totalPages"
          class="pagination-button"
        >
          {{ $t('sniffer.pagination.next') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { snifferService } from '../services/snifferService';

export default {
  name: 'SnifferView',
  setup() {
    const { t } = useI18n();
    const interfaces = ref([]);
    const selectedInterface = ref('');
    const selectedStatus = ref('');
    const writeToFile = ref(false);
    const activeSessions = ref([]);
    const validationErrors = ref({});
    const currentPage = ref(1);
    const itemsPerPage = 5;

    const totalPages = computed(() => {
      return Math.ceil(activeSessions.value.length / itemsPerPage);
    });

    const currentPageItems = computed(() => {
      const start = (currentPage.value - 1) * itemsPerPage;
      const end = start + itemsPerPage;
      return activeSessions.value.slice(start, end);
    });

    const nextPage = () => {
      if (currentPage.value < totalPages.value) {
        currentPage.value++;
      }
    };

    const previousPage = () => {
      if (currentPage.value > 1) {
        currentPage.value--;
      }
    };

    const isSniffing = computed(() => {
      return activeSessions.value.some(session => session.status === 'Running');
    });
    
    const protocols = [
      'ip',
      'ip6',
      'tcp',
      'udp',
      'icmp',
      'icmp6',
      'arp',
      'ether',
      'stp',
      'mpls',
      'sctp',
      'dccp',
      'ppp',
      'radio'
    ];

    const filter = ref({
      src_ip: '',
      dst_ip: '',
      protocol: '',
      src_port: null,
      dst_port: null
    });

    const hasValidationErrors = computed(() => {
      return Object.values(validationErrors.value).some(error => error !== '');
    });

    const validateIp = (field) => {
      const value = filter.value[field];
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
      const value = filter.value[field];
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

    const loadInterfaces = async () => {
      try {
        const interfacesList = await snifferService.getInterfaces();
        interfaces.value = interfacesList;
        if (interfaces.value.length > 0) {
          selectedInterface.value = interfaces.value[0];
        }
      } catch (error) {
        console.error('Error loading interfaces:', error);
      }
    };

    const startSniffing = async () => {
      if (hasValidationErrors.value) {
        return;
      }

      try {
        await snifferService.startSniffing(
          selectedInterface.value,
          writeToFile.value,
          filter.value
        );
        loadActiveSessions();
      } catch (error) {
        console.error('Error starting sniffing:', error);
      }
    };

    const stopSniffing = async () => {
      if (activeSessions.value.length > 0) {
        const session = activeSessions.value[0];
        await stopSession(session.sniff_id);
      }
    };

    const stopSession = async (sniffId) => {
      try {
        await snifferService.stopSniffing(sniffId);
        await new Promise(resolve => setTimeout(resolve, 500));
        await loadActiveSessions();
      } catch (error) {
        console.error('Error stopping session:', error);
      }
    };

    const handleStatusChange = async () => {
      currentPage.value = 1; // Reset to first page when changing status
      await refreshData();
    };

    const loadActiveSessions = async () => {
      try {
        let sessions;
        if (selectedStatus.value) {
          sessions = await snifferService.getSniffsByStatus(selectedStatus.value);
        } else {
          sessions = await snifferService.getActiveSessions();
        }
        // Sort sessions by start time, most recent first
        activeSessions.value = sessions.sort((a, b) => 
          new Date(b.start_at) - new Date(a.start_at)
        );
      } catch (error) {
        console.error('Error loading active sessions:', error);
        activeSessions.value = [];
      }
    };

    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleString();
    };

    const calculateDuration = (startTime, endTime) => {
      const start = new Date(startTime);
      const end = new Date(endTime);
      const diff = end - start;
      
      const seconds = Math.floor(diff / 1000);
      const minutes = Math.floor(seconds / 60);
      const hours = Math.floor(minutes / 60);
      
      const remainingSeconds = seconds % 60;
      const remainingMinutes = minutes % 60;
      
      let duration = '';
      if (hours > 0) duration += `${hours}h `;
      if (remainingMinutes > 0 || hours > 0) duration += `${remainingMinutes}m `;
      duration += `${remainingSeconds}s`;
      
      return duration;
    };

    const refreshData = async () => {
      console.log('Refreshing data...');
      await loadInterfaces();
      await loadActiveSessions();
    };

    const clearCache = async () => {
      try {
        await snifferService.clearCache();
        // Refresh the data after clearing cache
        await refreshData();
      } catch (error) {
        console.error('Failed to clear cache:', error);
      }
    };

    onMounted(async () => {
      await refreshData();
    });

    return {
      interfaces,
      selectedInterface,
      selectedStatus,
      writeToFile,
      isSniffing,
      activeSessions,
      validationErrors,
      filter,
      protocols,
      hasValidationErrors,
      currentPage,
      totalPages,
      currentPageItems,
      nextPage,
      previousPage,
      validateIp,
      validatePort,
      loadInterfaces,
      startSniffing,
      stopSniffing,
      stopSession,
      refreshData,
      handleStatusChange,
      formatDate,
      calculateDuration,
      clearCache,
    };
  }
};
</script>

<style scoped>
.sniffer-view {
  padding: 20px;
}

.control-panel {
  background-color: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
}

.filter-params {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
}

.input-group {
  display: flex;
  flex-direction: column;
}

.input-group label {
  margin-bottom: 5px;
  font-weight: bold;
}

.input-group input,
.input-group select {
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
}

.button-group {
  display: flex;
  gap: 10px;
  margin-top: 20px;
}

button {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  background-color: #3498db;
  color: white;
  transition: all 0.3s;
}

button:hover:not(:disabled) {
  background-color: #2980b9;
}

button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.status-panel {
  background-color: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.sessions-list {
  display: grid;
  gap: 15px;
}

.session-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.session-info {
  flex: 1;
}

.no-sessions {
  text-align: center;
  padding: 20px;
  color: #7f8c8d;
}

.status-running {
  color: #2ecc71;
  font-weight: bold;
}

.status-stopped {
  color: #e74c3c;
  font-weight: bold;
}

.checkbox-group {
  display: flex;
  align-items: center;
  margin: 10px 0;
}

.custom-checkbox {
  width: 20px;
  height: 20px;
  margin-right: 10px;
  cursor: pointer;
}

.checkbox-label {
  font-size: 1.1em;
  cursor: pointer;
}

.status-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.header-controls {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.status-filter {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.status-filter select {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  background-color: white;
}

.refresh-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background-color: #2ecc71 !important;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.refresh-button:hover {
  background-color: #27ae60 !important;
}

.refresh-icon {
  font-size: 1.2em;
  transition: transform 0.3s;
}

.refresh-button:hover .refresh-icon {
  transform: rotate(180deg);
}

.pagination-controls {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  margin-top: 20px;
  padding: 10px;
}

.pagination-button {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  background-color: #3498db;
  color: white;
  cursor: pointer;
  transition: background-color 0.3s;
}

.pagination-button:hover:not(:disabled) {
  background-color: #2980b9;
}

.pagination-button:disabled {
  background-color: #95a5a6;
  cursor: not-allowed;
  opacity: 1;
}

.page-info {
  font-size: 14px;
  color: #666;
}

.header-buttons {
  display: flex;
  gap: 10px;
  align-items: center;
}

.clear-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background-color: #e74c3c !important;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.clear-button:hover {
  background-color: #c0392b !important;
}

.clear-button i {
  font-size: 1.2em;
}
</style> 