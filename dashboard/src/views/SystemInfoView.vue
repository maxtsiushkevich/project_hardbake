<template>
  <div class="system-info-view">
    <h2>{{ $t('systemInfo.title') }}</h2>
    
    <div class="interfaces-panel">
      <div class="panel-header">
        <h3>{{ $t('systemInfo.interfaces.title') }}</h3>
      </div>
      <div class="refresh-container">
        <button @click="loadInterfaces" class="refresh-button">
          <span class="refresh-icon">↻</span>
          {{ $t('systemInfo.buttons.refresh') }}
        </button>
      </div>
      
      <div v-if="loading" class="loading">
        {{ $t('systemInfo.interfaces.loading') }}
      </div>
      
      <div v-else-if="error" class="error-message">
        {{ error }}
      </div>
      
      <div v-else-if="interfaces.length === 0" class="no-interfaces">
        {{ $t('systemInfo.interfaces.noInterfaces') }}
      </div>
      
      <div v-else class="interfaces-list">
        <div v-for="iface in interfaces" :key="iface.name" class="interface-card">
          <div class="interface-header">
            <h4>{{ iface.name }}</h4>
            <button @click="toggleDetails(iface.name)">
              {{ showDetails[iface.name] ? $t('systemInfo.interfaces.hideDetails') : $t('systemInfo.interfaces.showDetails') }}
            </button>
          </div>
          
          <div v-if="showDetails[iface.name]" class="interface-details">
            <div class="info-section">
              <h5>{{ $t('systemInfo.interfaces.networkInfo') }}</h5>
              <div v-if="iface.info.IPv4">
                <span class="label">{{ $t('systemInfo.interfaces.ipv4') }}:</span>
                <span class="value">{{ iface.info.IPv4 }}</span>
              </div>
              <div v-if="iface.info.IPv4_netmask">
                <span class="label">{{ $t('systemInfo.interfaces.netmask') }}:</span>
                <span class="value">{{ iface.info.IPv4_netmask }}</span>
              </div>
              <div v-if="iface.info.IPv6">
                <span class="label">{{ $t('systemInfo.interfaces.ipv6') }}:</span>
                <span class="value">{{ iface.info.IPv6 }}</span>
              </div>
              <div v-if="iface.info.mac">
                <span class="label">{{ $t('systemInfo.interfaces.mac') }}:</span>
                <span class="value">{{ iface.info.mac }}</span>
              </div>
            </div>
            
            <div class="stats-section">
              <h5>{{ $t('systemInfo.interfaces.statistics') }}</h5>
              <div>
                <span class="label">{{ $t('systemInfo.interfaces.bytesSent') }}:</span>
                <span class="value">{{ formatBytes(iface.stats.bytes_sent) }}</span>
              </div>
              <div>
                <span class="label">{{ $t('systemInfo.interfaces.bytesReceived') }}:</span>
                <span class="value">{{ formatBytes(iface.stats.bytes_received) }}</span>
              </div>
              <div>
                <span class="label">{{ $t('systemInfo.interfaces.packetsSent') }}:</span>
                <span class="value">{{ iface.stats.packets_sent }}</span>
              </div>
              <div>
                <span class="label">{{ $t('systemInfo.interfaces.packetsReceived') }}:</span>
                <span class="value">{{ iface.stats.packets_received }}</span>
              </div>
              <div>
                <span class="label">{{ $t('systemInfo.interfaces.errorsIn') }}:</span>
                <span class="value">{{ iface.stats.errors_in }}</span>
              </div>
              <div>
                <span class="label">{{ $t('systemInfo.interfaces.errorsOut') }}:</span>
                <span class="value">{{ iface.stats.errors_out }}</span>
              </div>
              <div>
                <span class="label">{{ $t('systemInfo.interfaces.droppedIn') }}:</span>
                <span class="value">{{ iface.stats.dropped_in }}</span>
              </div>
              <div>
                <span class="label">{{ $t('systemInfo.interfaces.droppedOut') }}:</span>
                <span class="value">{{ iface.stats.dropped_out }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { systemInfoApi } from '../services/api';

export default {
  name: 'SystemInfoView',
  setup() {
    const { t } = useI18n();
    const interfaces = ref([]);
    const showDetails = ref({});
    const loading = ref(false);
    const error = ref(null);

    const loadInterfaces = async () => {
      loading.value = true;
      error.value = null;
      try {
        const response = await systemInfoApi.get('/interfaces/all');
        interfaces.value = response.data;
        // Initialize showDetails for each interface
        interfaces.value.forEach(iface => {
          showDetails.value[iface.name] = false;
        });
      } catch (err) {
        if (err.response?.status === 404) {
          error.value = t('systemInfo.errors.notFound');
        } else if (err.response?.status === 422) {
          error.value = t('systemInfo.errors.invalidRequest');
        } else {
          error.value = t('systemInfo.errors.loadFailed');
        }
        console.error('Error loading interfaces:', err);
      } finally {
        loading.value = false;
      }
    };

    const toggleDetails = (interfaceName) => {
      showDetails.value[interfaceName] = !showDetails.value[interfaceName];
    };

    const formatBytes = (bytes) => {
      if (bytes === 0) return '0 Bytes';
      const k = 1024;
      const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };

    onMounted(() => {
      loadInterfaces();
    });

    return {
      interfaces,
      showDetails,
      loading,
      error,
      toggleDetails,
      formatBytes,
      loadInterfaces
    };
  }
};
</script>

<style scoped>
.system-info-view {
  padding: 20px;
}

.interfaces-panel {
  background-color: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.interfaces-list {
  display: grid;
  gap: 15px;
}

.interface-card {
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 15px;
}

.interface-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.interface-details {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #eee;
}

.info-section, .stats-section {
  padding: 10px;
  background-color: #f8f9fa;
  border-radius: 4px;
}

h5 {
  margin-bottom: 10px;
  color: #2c3e50;
}

.label {
  font-weight: bold;
  color: #34495e;
  margin-right: 10px;
}

.value {
  color: #2c3e50;
}

button {
  padding: 8px 15px;
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

.loading {
  text-align: center;
  padding: 20px;
  color: #7f8c8d;
}

.error-message {
  text-align: center;
  padding: 20px;
  color: #e74c3c;
  background-color: #fadbd8;
  border-radius: 4px;
  margin: 10px 0;
}

.no-interfaces {
  text-align: center;
  padding: 20px;
  color: #7f8c8d;
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
  background-color: #27ae60;
}

.refresh-icon {
  font-size: 1.2em;
  transition: transform 0.3s;
}

.refresh-button:hover .refresh-icon {
  transform: rotate(180deg);
}

.refresh-container {
  display: flex;
  justify-content: flex-start;
  margin-bottom: 20px;
}
</style> 