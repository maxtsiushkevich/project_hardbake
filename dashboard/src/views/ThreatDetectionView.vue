<template>
  <div class="threat-detection-view">
    <h2>{{ $t('threatDetection.title') }}</h2>
    
    <div class="control-panel">
      <div class="detection-section">
        <h3>{{ $t('threatDetection.detection.title') }}</h3>
        <div class="button-group">
          <button @click="startDetection" :disabled="detectionStatus === 'Running'">{{ $t('threatDetection.detection.start') }}</button>
          <button @click="stopDetection" :disabled="detectionStatus !== 'Running'">{{ $t('threatDetection.detection.stop') }}</button>
        </div>
        <div class="status-indicator-row">
          <div class="status-indicator" :class="statusClass">
            {{ detectionStatus }}
          </div>
          <button @click="loadStatus" class="refresh-button" :title="$t('threatDetection.buttons.refresh')">
            <span class="refresh-icon">↻</span>
          </button>
        </div>
        <div v-if="error" class="error-message">
          {{ $t('common.error') }}: {{ error }}
        </div>
      </div>

      <div class="batch-section">
        <h3>{{ $t('threatDetection.batch.title') }}</h3>
        <div class="settings-group">
          <div class="setting">
            <label>{{ $t('threatDetection.batch.label') }}:</label>
            <input type="number" v-model.number="batchSize" min="1">
            <button @click="updateBatchSize">{{ $t('threatDetection.batch.update') }}</button>
          </div>
        </div>
        <div class="current-batch-size">
          {{ $t('threatDetection.batch.current') }}: {{ currentBatchSize }}
        </div>
      </div>

      <div class="model-section">
        <h3>{{ $t('threatDetection.model.title') }}</h3>
        <div class="button-group">
          <input type="file" @change="handleModelUpload" accept=".joblib" style="display: none" ref="modelInput">
          <button @click="triggerModelUpload">{{ $t('threatDetection.model.upload') }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { threatDetectionApi } from '../services/api';

export default {
  name: 'ThreatDetectionView',
  setup() {
    const { t } = useI18n();
    const detectionStatus = ref(t('threatDetection.detection.notRunning'));
    const error = ref(null);
    const batchSize = ref(100);
    const currentBatchSize = ref(100);
    const modelInput = ref(null);

    const startDetection = async () => {
      try {
        await threatDetectionApi.post('/detect/start');
        loadStatus();
      } catch (error) {
        console.error('Error starting detection:', error);
        error.value = t('threatDetection.errors.startFailed');
      }
    };

    const stopDetection = async () => {
      try {
        await threatDetectionApi.post('/detect/stop');
        loadStatus();
      } catch (error) {
        console.error('Error stopping detection:', error);
        error.value = t('threatDetection.errors.stopFailed');
      }
    };

    const updateBatchSize = async () => {
      try {
        await threatDetectionApi.patch('/detect/set_batch_size', null, {
          params: { size: batchSize.value }
        });
        loadBatchSize();
      } catch (error) {
        console.error('Error updating batch size:', error);
        error.value = t('threatDetection.errors.batchSizeUpdateFailed');
      }
    };

    const handleModelUpload = async (event) => {
      const file = event.target.files[0];
      if (!file) return;

      const formData = new FormData();
      formData.append('file', file);

      try {
        await threatDetectionApi.post('/detect/upload_models/', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });
      } catch (error) {
        console.error('Error uploading models:', error);
        error.value = t('threatDetection.errors.modelUploadFailed');
      }
    };

    const triggerModelUpload = () => {
      modelInput.value.click();
    };

    const loadStatus = async () => {
      try {
        const response = await threatDetectionApi.get('/detect/status');
        detectionStatus.value = response.data.status;
        error.value = response.data.error;
      } catch (error) {
        console.error('Error loading status:', error);
        error.value = t('threatDetection.errors.statusLoadFailed');
      }
    };

    const loadBatchSize = async () => {
      try {
        const response = await threatDetectionApi.get('/detect/get_batch_size');
        currentBatchSize.value = response.data.size;
        batchSize.value = response.data.size;
      } catch (error) {
        console.error('Error loading batch size:', error);
        error.value = t('threatDetection.errors.batchSizeLoadFailed');
      }
    };

    const statusClass = computed(() => {
      return {
        'status-running': detectionStatus.value === 'Running',
        'status-stopped': detectionStatus.value === 'Stopped',
        'status-error': detectionStatus.value === 'Error',
        'status-not-running': detectionStatus.value === 'Not running'
      };
    });

    onMounted(() => {
      loadStatus();
      loadBatchSize();
    });

    return {
      detectionStatus,
      error,
      batchSize,
      currentBatchSize,
      modelInput,
      startDetection,
      stopDetection,
      updateBatchSize,
      handleModelUpload,
      triggerModelUpload,
      loadStatus,
      statusClass
    };
  }
};
</script>

<style scoped>
.threat-detection-view {
  padding: 20px;
}

.control-panel {
  background-color: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.detection-section, .batch-section, .model-section {
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #eee;
}

.settings-group {
  margin: 15px 0;
}

.setting {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.setting input {
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  width: 100px;
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

.error-message {
  color: #e74c3c;
  margin-top: 10px;
  padding: 5px;
  background-color: #fadbd8;
  border-radius: 4px;
}

.current-batch-size {
  padding: 10px;
  background-color: #f8f9fa;
  border-radius: 4px;
  margin-top: 10px;
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
</style> 