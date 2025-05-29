<template>
  <div class="packet-processor-view">
    <h2>{{ $t('packetProcessor.title') }}</h2>
    
    <div class="control-panel">
      <div class="upload-section">
        <h3>{{ $t('packetProcessor.upload.title') }}</h3>
        <div class="file-upload-group">
          <label class="file-upload-label">
            <input type="file" @change="handleFileUpload" accept=".pcap,.pcapng" class="file-input">
            <span class="file-upload-text">{{ selectedFile ? selectedFile.name : $t('packetProcessor.upload.chooseFile') }}</span>
          </label>
          <button @click="uploadFile" :disabled="!selectedFile" class="upload-button">{{ $t('packetProcessor.upload.button') }}</button>
        </div>
      </div>
    </div>

    <div class="uploads-panel">
      <h3>{{ $t('packetProcessor.uploads.title') }}</h3>
      <div class="filter-controls">
        <div class="input-group">
          <select 
            id="statusFilter" 
            v-model="selectedStatus" 
            @change="loadUploads"
          >
            <option value="">{{ $t('packetProcessor.filter.allStatuses') }}</option>
            <option value="Running">{{ $t('packetProcessor.filter.running') }}</option>
            <option value="Processed">{{ $t('packetProcessor.filter.processed') }}</option>
            <option value="Crashed">{{ $t('packetProcessor.filter.crashed') }}</option>
          </select>
        </div>
        <div class="header-buttons">
          <button @click="clearCache" class="clear-button">
            ⌫ {{ $t('packetProcessor.buttons.clear') }}
          </button>
          <button @click="loadUploads" class="refresh-button">
            <span class="refresh-icon">↻</span> {{ $t('packetProcessor.buttons.refresh') }}
          </button>
        </div>
      </div>
      <div v-if="uploads.length === 0" class="no-uploads">
        {{ $t('packetProcessor.uploads.noUploads') }}
      </div>
      <div v-else class="uploads-list">
        <div v-for="upload in currentPageItems" :key="upload.upload_id" class="upload-card">
          <div class="upload-info">
            <div>{{ $t('packetProcessor.uploads.uploadId') }}: {{ upload.upload_id }}</div>
            <div>{{ $t('packetProcessor.uploads.status') }}: <span :class="getStatusClass(upload.status)">{{ upload.status }}</span></div>
            <div>{{ $t('packetProcessor.uploads.tcpSessions') }}: {{ upload.tcp_sessions }}</div>
            <div>{{ $t('packetProcessor.uploads.udpSessions') }}: {{ upload.udp_sessions }}</div>
          </div>
          <div class="upload-actions">
            <div class="rmq-action">
              <button @click="sendToRmq(upload.upload_id)" :disabled="upload.status !== 'Processed'">{{ $t('packetProcessor.uploads.sendToRmq') }}</button>
              <div v-if="rmqErrors[upload.upload_id]" class="rmq-error">
                {{ rmqErrors[upload.upload_id] }}
              </div>
            </div>
          </div>
        </div>
      </div>
      <div v-if="uploads.length > 0" class="pagination-controls">
        <button 
          @click="previousPage" 
          :disabled="currentPage === 1"
          class="pagination-button"
        >
          {{ $t('packetProcessor.buttons.previous') }}
        </button>
        <span class="page-info">{{ $t('packetProcessor.pagination.page') }} {{ currentPage }} {{ $t('packetProcessor.pagination.of') }} {{ totalPages }}</span>
        <button 
          @click="nextPage" 
          :disabled="currentPage === totalPages"
          class="pagination-button"
        >
          {{ $t('packetProcessor.buttons.next') }}
        </button>
      </div>
    </div>

    <div class="management-panel">
      <h3>{{ $t('packetProcessor.consumer.title') }}</h3>
      <div class="button-group">
        <button @click="startConsumer" :disabled="consumerStatus === 'Running'">{{ $t('packetProcessor.consumer.start') }}</button>
        <button @click="stopConsumer" :disabled="consumerStatus !== 'Running'">{{ $t('packetProcessor.consumer.stop') }}</button>
      </div>
      <div class="status-indicator-row">
        <div class="status-indicator" :class="statusClass">
          {{ consumerStatus }}
        </div>
        <button @click="loadConsumerStatus" class="refresh-button" :title="$t('packetProcessor.buttons.refresh')">
          <span class="refresh-icon">↻</span>
        </button>
      </div>
      <div v-if="error" class="error-message">
        {{ $t('common.error') }}: {{ error }}
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { packetProcessorService } from '../services/packetProcessorService';

export default {
  name: 'PacketProcessorView',
  setup() {
    const { t } = useI18n();
    const selectedFile = ref(null);
    const consumerStatus = ref(t('packetProcessor.consumer.notRunning'));
    const error = ref(null);
    const uploads = ref([]);
    const selectedStatus = ref('');
    const rmqErrors = ref({});
    const currentPage = ref(1);
    const itemsPerPage = 5;

    const totalPages = computed(() => {
      return Math.ceil(uploads.value.length / itemsPerPage);
    });

    const currentPageItems = computed(() => {
      const start = (currentPage.value - 1) * itemsPerPage;
      const end = start + itemsPerPage;
      return uploads.value.slice(start, end);
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

    const handleFileUpload = (event) => {
      selectedFile.value = event.target.files[0];
    };

    const uploadFile = async () => {
      if (!selectedFile.value) return;

      try {
        await packetProcessorService.uploadPcapFile(selectedFile.value);
        selectedFile.value = null;
        loadUploads();
      } catch (error) {
        console.error('Error uploading file:', error);
        error.value = t('packetProcessor.errors.uploadFailed');
      }
    };

    const loadUploads = async () => {
      try {
        currentPage.value = 1;
        if (selectedStatus.value) {
          uploads.value = await packetProcessorService.getSniffsByStatus(selectedStatus.value);
        } else {
          uploads.value = await packetProcessorService.getAllUploads();
        }
      } catch (error) {
        console.error('Error loading uploads:', error);
        error.value = t('packetProcessor.errors.loadFailed');
      }
    };

    const sendToRmq = async (uploadId) => {
      try {
        rmqErrors.value[uploadId] = null;
        await packetProcessorService.sendStreamsToRmq(uploadId);
        loadUploads();
      } catch (error) {
        console.error('Error sending to RMQ:', error);
        if (error.response?.data?.detail) {
          rmqErrors.value[uploadId] = error.response.data.detail;
        } else {
          rmqErrors.value[uploadId] = t('packetProcessor.errors.rmqFailed');
        }
      }
    };

    const startConsumer = async () => {
      try {
        await packetProcessorService.startConsumer();
        loadConsumerStatus();
      } catch (error) {
        console.error('Error starting consumer:', error);
        error.value = t('packetProcessor.errors.consumerStartFailed');
      }
    };

    const stopConsumer = async () => {
      try {
        await packetProcessorService.stopConsumer();
        loadConsumerStatus();
      } catch (error) {
        console.error('Error stopping consumer:', error);
        error.value = t('packetProcessor.errors.consumerStopFailed');
      }
    };

    const loadConsumerStatus = async () => {
      try {
        const response = await packetProcessorService.getConsumerStatus();
        consumerStatus.value = response.status;
        error.value = response.error;
      } catch (error) {
        console.error('Error loading consumer status:', error);
        error.value = t('packetProcessor.errors.statusLoadFailed');
      }
    };

    const getStatusClass = (status) => {
      return {
        'status-running': status === 'Running',
        'status-processed': status === 'Processed',
        'status-crashed': status === 'Crashed'
      };
    };

    const clearCache = async () => {
      try {
        await packetProcessorService.clearCache();
        await loadUploads();
      } catch (error) {
        console.error('Error clearing cache:', error);
        error.value = t('packetProcessor.errors.clearCacheFailed');
      }
    };

    const statusClass = computed(() => {
      return {
        'status-running': consumerStatus.value === 'Running',
        'status-stopped': consumerStatus.value === 'Stopped',
        'status-error': consumerStatus.value === 'Error',
        'status-not-running': consumerStatus.value === 'Not running'
      };
    });

    onMounted(() => {
      loadConsumerStatus();
      loadUploads();
    });

    return {
      selectedFile,
      consumerStatus,
      error,
      uploads,
      selectedStatus,
      rmqErrors,
      currentPage,
      totalPages,
      currentPageItems,
      nextPage,
      previousPage,
      handleFileUpload,
      uploadFile,
      loadUploads,
      sendToRmq,
      startConsumer,
      stopConsumer,
      loadConsumerStatus,
      getStatusClass,
      clearCache,
      statusClass
    };
  }
};
</script>

<style scoped>
.packet-processor-view {
  padding: 20px;
}

.control-panel {
  background-color: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
}

.upload-section, .status-section {
  margin-bottom: 20px;
}

.status-card {
  padding: 15px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background-color: #f8f9fa;
}

.no-status {
  text-align: center;
  padding: 20px;
  color: #7f8c8d;
}

.uploads-panel {
  background-color: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
}

.filter-controls {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 15px;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.input-group label {
  font-weight: 600;
  color: #2c3e50;
}

.input-group select {
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1em;
  background-color: white;
  cursor: pointer;
  min-width: 200px;
}

.input-group select:focus {
  outline: none;
  border-color: #3498db;
  box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.2);
}

.uploads-list {
  display: grid;
  gap: 15px;
}

.upload-card {
  padding: 15px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background-color: #f8f9fa;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.upload-info {
  flex: 1;
}

.upload-actions {
  display: flex;
  gap: 10px;
}

.management-panel {
  background-color: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.button-group {
  display: flex;
  gap: 10px;
  margin: 15px 0;
}

.status-display {
  padding: 10px;
  background-color: #f8f9fa;
  border-radius: 4px;
  margin-top: 10px;
}

.status-indicator-row {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 10px;
  margin: 10px 0;
}

.status-indicator {
  display: inline-block;
  padding: 8px 16px;
  border-radius: 4px;
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

.error-message {
  color: #e74c3c;
  margin-top: 10px;
  padding: 10px;
  background-color: #fadbd8;
  border-radius: 4px;
}

.rmq-action {
  position: relative;
  display: inline-block;
}

.rmq-error {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 5px;
  color: #e74c3c;
  padding: 5px 10px;
  background-color: #fadbd8;
  border-radius: 4px;
  font-size: 0.9em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 300px;
  z-index: 1;
}

.file-upload-group {
  display: flex;
  gap: 10px;
  align-items: center;
}

.file-upload-label {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  background-color: white;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s ease;
  min-width: 200px;
}

.file-upload-label:hover {
  border-color: #3498db;
  background-color: #f8f9fa;
}

.file-input {
  display: none;
}

.file-upload-text {
  color: #2c3e50;
  font-size: 1.1em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.upload-button {
  padding: 8px 16px;
  background-color: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
  font-size: 1.1em;
}

.upload-button:hover {
  background-color: #2980b9;
}

.upload-button:disabled {
  background-color: #95a5a6;
  cursor: not-allowed;
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
  padding: 5px 10px;
  background-color: #e74c3c !important;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
  font-size: 1em;
}

.clear-button:hover {
  background-color: #c0392b !important;
}
</style> 