<template>
  <div class="ml-data-processor-view">
    <h2>{{ $t('mlDataProcessor.title') }}</h2>
    
    <div class="control-panel">
      <h3>{{ $t('mlDataProcessor.consumer.title') }}</h3>
      <div class="button-group">
        <button @click="startConsumer" :disabled="consumerStatus === 'Running'">{{ $t('mlDataProcessor.consumer.start') }}</button>
        <button @click="stopConsumer" :disabled="consumerStatus !== 'Running'">{{ $t('mlDataProcessor.consumer.stop') }}</button>
      </div>
      <!-- <div class="status-display"> -->
        <div class="status-indicator-row">
          <div class="status-indicator" :class="statusClass">
            {{ consumerStatus }}
          </div>
          <button @click="loadConsumerStatus" class="refresh-button" :title="$t('mlDataProcessor.buttons.refresh')">
            <span class="refresh-icon">↻</span>
          </button>
        </div>
        <div v-if="error" class="error-message">
          {{ $t('common.error') }}: {{ error }}
        </div>
      <!-- </div> -->
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { mlDataProcessorApi } from '../services/api';

export default {
  name: 'MLDataProcessorView',
  setup() {
    const { t } = useI18n();
    const consumerStatus = ref(t('mlDataProcessor.consumer.notRunning'));
    const error = ref(null);

    const startConsumer = async () => {
      try {
        await mlDataProcessorApi.post('/management/start');
        loadConsumerStatus();
      } catch (error) {
        console.error('Error starting consumer:', error);
        error.value = t('mlDataProcessor.errors.startFailed');
      }
    };

    const stopConsumer = async () => {
      try {
        await mlDataProcessorApi.post('/management/stop');
        loadConsumerStatus();
      } catch (error) {
        console.error('Error stopping consumer:', error);
        error.value = t('mlDataProcessor.errors.stopFailed');
      }
    };

    const loadConsumerStatus = async () => {
      try {
        const response = await mlDataProcessorApi.get('/management/status');
        consumerStatus.value = response.data.status;
        error.value = response.data.error;
      } catch (error) {
        console.error('Error loading consumer status:', error);
        error.value = t('mlDataProcessor.errors.statusLoadFailed');
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
    });

    return {
      consumerStatus,
      error,
      startConsumer,
      stopConsumer,
      loadConsumerStatus,
      statusClass
    };
  }
};
</script>

<style scoped>
.ml-data-processor-view {
  padding: 20px;
}

.control-panel {
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

.error-message {
  color: #e74c3c;
  margin-top: 10px;
  padding: 5px;
  background-color: #fadbd8;
  border-radius: 4px;
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