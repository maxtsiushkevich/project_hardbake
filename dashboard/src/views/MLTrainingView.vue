<template>
  <div class="ml-training-view">
    <h2>{{ $t('mlTraining.title') }}</h2>
    
    <div class="control-panel">
      <div class="consumer-section">
        <h3>{{ $t('mlTraining.consumer.title') }}</h3>
        <div class="button-group">
          <button @click="startConsuming" :disabled="consumerStatus === 'Running'">{{ $t('mlTraining.consumer.start') }}</button>
          <button @click="stopConsuming" :disabled="consumerStatus !== 'Running'">{{ $t('mlTraining.consumer.stop') }}</button>
        </div>
        <div class="status-indicator-row">
          <div class="status-indicator" :class="statusClass">
            {{ consumerStatus }}
          </div>
          <button @click="loadConsumerStatus" class="refresh-button" :title="$t('mlTraining.buttons.refresh')">
            <span class="refresh-icon">↻</span>
          </button>
        </div>
      </div>

      <div class="training-section">
        <h3>{{ $t('mlTraining.training.title') }}</h3>
        <div class="settings-group">
          <div class="setting">
            <label>{{ $t('mlTraining.training.minSamples') }}:</label>
            <input type="number" v-model.number="minSamplesInput" min="1">
            <button @click="updateMinSamples">{{ $t('mlTraining.training.update') }}</button>
          </div>
        </div>
        <div class="button-group">
          <button @click="startTraining" :disabled="!canTrain">{{ $t('mlTraining.training.start') }}</button>
        </div>
        <div class="status-display">
          <div class="status-row">
            <div>
              <div>{{ $t('mlTraining.training.status') }}: {{ trainingStatus }}</div>
              <div>{{ $t('mlTraining.training.collectedSamples') }}: {{ collectedSamples }}</div>
              <div>{{ $t('mlTraining.training.requiredSamples') }}: {{ minSamples }}</div>
            </div>
            <button @click="loadTrainingStatus" class="refresh-button">
              <span class="refresh-icon">↻</span>
            </button>
          </div>
        </div>
      </div>

      <div class="model-settings-section">
        <h3>{{ $t('mlTraining.modelSettings.title') }}</h3>
        <div class="button-group">
          <button @click="loadCurrentSettings" class="refresh-button">
            <span class="refresh-icon">↻</span>
            {{ $t('mlTraining.modelSettings.refresh') }}
          </button>
        </div>
        <div class="settings-group">
          <div class="model-card">
            <div class="model-header">
              <h4>{{ $t('mlTraining.modelSettings.isolationForest.title') }}</h4>
              <button class="update-button" @click="openUpdateModal('isolation_forest')">{{ $t('mlTraining.modelSettings.isolationForest.updateParams') }}</button>
            </div>
            <p class="model-description">{{ $t('mlTraining.modelSettings.isolationForest.description') }}</p>
            <div class="hyperparameter-display">
              <div class="param-row">
                <span class="param-name">{{ $t('mlTraining.modelSettings.isolationForest.params.nEstimators.name') }}:</span>
                <span class="param-value">{{ modelSettings.hyperparameters?.isolation_forest?.n_estimators }}</span>
                <span class="param-description">{{ $t('mlTraining.modelSettings.isolationForest.params.nEstimators.description') }}</span>
              </div>
              <div class="param-row">
                <span class="param-name">{{ $t('mlTraining.modelSettings.isolationForest.params.contamination.name') }}:</span>
                <span class="param-value">{{ modelSettings.hyperparameters?.isolation_forest?.contamination }}</span>
                <span class="param-description">{{ $t('mlTraining.modelSettings.isolationForest.params.contamination.description') }}</span>
              </div>
              <div class="param-row">
                <span class="param-name">{{ $t('mlTraining.modelSettings.isolationForest.params.nJobs.name') }}:</span>
                <span class="param-value">{{ modelSettings.hyperparameters?.isolation_forest?.n_jobs }}</span>
                <span class="param-description">{{ $t('mlTraining.modelSettings.isolationForest.params.nJobs.description') }}</span>
              </div>
            </div>
          </div>

          <div class="model-card">
            <div class="model-header">
              <h4>{{ $t('mlTraining.modelSettings.oneClassSvm.title') }}</h4>
              <button class="update-button" @click="openUpdateModal('one_class_svm')">{{ $t('mlTraining.modelSettings.oneClassSvm.updateParams') }}</button>
            </div>
            <p class="model-description">{{ $t('mlTraining.modelSettings.oneClassSvm.description') }}</p>
            <div class="hyperparameter-display">
              <div class="param-row">
                <span class="param-name">{{ $t('mlTraining.modelSettings.oneClassSvm.params.nu.name') }}:</span>
                <span class="param-value">{{ modelSettings.hyperparameters?.one_class_svm?.nu }}</span>
                <span class="param-description">{{ $t('mlTraining.modelSettings.oneClassSvm.params.nu.description') }}</span>
              </div>
              <div class="param-row">
                <span class="param-name">{{ $t('mlTraining.modelSettings.oneClassSvm.params.kernel.name') }}:</span>
                <span class="param-value">{{ modelSettings.hyperparameters?.one_class_svm?.kernel }}</span>
                <span class="param-description">{{ $t('mlTraining.modelSettings.oneClassSvm.params.kernel.description') }}</span>
              </div>
              <div class="param-row">
                <span class="param-name">{{ $t('mlTraining.modelSettings.oneClassSvm.params.gamma.name') }}:</span>
                <span class="param-value">{{ modelSettings.hyperparameters?.one_class_svm?.gamma }}</span>
                <span class="param-description">{{ $t('mlTraining.modelSettings.oneClassSvm.params.gamma.description') }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Update Parameters Modal -->
      <div v-if="showUpdateModal" class="modal-overlay" @click="closeUpdateModal">
        <div class="modal-content" @click.stop>
          <div class="modal-header">
            <h3>{{ $t('mlTraining.modal.updateParams') }} {{ currentModel === 'isolation_forest' ? $t('mlTraining.modelSettings.isolationForest.title') : $t('mlTraining.modelSettings.oneClassSvm.title') }}</h3>
            <button class="close-button" @click="closeUpdateModal">&times;</button>
          </div>
          <div class="modal-body">
            <div v-if="currentModel === 'isolation_forest'" class="parameter-inputs">
              <div class="input-group">
                <label>{{ $t('mlTraining.modelSettings.isolationForest.params.nEstimators.name') }}:</label>
                <input type="number" v-model.number="tempParams.isolation_forest.n_estimators" min="1">
                <div v-if="validationErrors.isolation_forest.n_estimators" class="error-message">
                  {{ validationErrors.isolation_forest.n_estimators }}
                </div>
              </div>
              <div class="input-group">
                <label>{{ $t('mlTraining.modelSettings.isolationForest.params.contamination.name') }}:</label>
                <input type="number" v-model.number="tempParams.isolation_forest.contamination" min="0" max="1" step="0.01">
                <div v-if="validationErrors.isolation_forest.contamination" class="error-message">
                  {{ validationErrors.isolation_forest.contamination }}
                </div>
              </div>
              <div class="input-group">
                <label>{{ $t('mlTraining.modelSettings.isolationForest.params.nJobs.name') }}:</label>
                <input type="number" v-model.number="tempParams.isolation_forest.n_jobs" min="-1">
                <div v-if="validationErrors.isolation_forest.n_jobs" class="error-message">
                  {{ validationErrors.isolation_forest.n_jobs }}
                </div>
              </div>
            </div>
            <div v-else class="parameter-inputs">
              <div class="input-group">
                <label>{{ $t('mlTraining.modelSettings.oneClassSvm.params.nu.name') }}:</label>
                <input type="number" v-model.number="tempParams.one_class_svm.nu" min="0" max="1" step="0.01">
                <div v-if="validationErrors.one_class_svm.nu" class="error-message">
                  {{ validationErrors.one_class_svm.nu }}
                </div>
              </div>
              <div class="input-group">
                <label>{{ $t('mlTraining.modelSettings.oneClassSvm.params.kernel.name') }}:</label>
                <select v-model="tempParams.one_class_svm.kernel">
                  <option value="rbf">RBF</option>
                  <option value="poly">Polynomial</option>
                  <option value="sigmoid">Sigmoid</option>
                </select>
                <div v-if="validationErrors.one_class_svm.kernel" class="error-message">
                  {{ validationErrors.one_class_svm.kernel }}
                </div>
              </div>
              <div class="input-group">
                <label>{{ $t('mlTraining.modelSettings.oneClassSvm.params.gamma.name') }}:</label>
                <input type="text" v-model="tempParams.one_class_svm.gamma">
                <div v-if="validationErrors.one_class_svm.gamma" class="error-message">
                  {{ validationErrors.one_class_svm.gamma }}
                </div>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button class="cancel-button" @click="closeUpdateModal">{{ $t('mlTraining.modal.cancel') }}</button>
            <button class="save-button" @click="updateHyperparameters">{{ $t('mlTraining.modal.save') }}</button>
          </div>
        </div>
      </div>

      <div class="model-section">
        <h3>{{ $t('mlTraining.modelManagement.title') }}</h3>
        <div class="button-group">
          <button @click="downloadModels" :disabled="trainingStatus !== 'Ready'">{{ $t('mlTraining.modelManagement.download') }}</button>
          <input type="file" @change="handleModelUpload" accept=".joblib" style="display: none" ref="modelInput">
          <button @click="triggerModelUpload">{{ $t('mlTraining.modelManagement.upload') }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { mlTrainingApi } from '../services/api';

export default {
  name: 'MLTrainingView',
  setup() {
    const { t } = useI18n();
    const consumerStatus = ref('Not running');
    const trainingStatus = ref('Not started');
    const collectedSamples = ref(0);
    const minSamples = ref(1000);
    const minSamplesInput = ref(1000);
    const modelInput = ref(null);
    const modelSettings = ref({
      hyperparameters: {
        isolation_forest: {
          n_estimators: 100,
          contamination: 0.15,
          n_jobs: -1
        },
        one_class_svm: {
          nu: 0.05,
          kernel: 'rbf',
          gamma: 'auto'
        }
      }
    });

    const showUpdateModal = ref(false);
    const currentModel = ref('');
    const tempParams = ref({
      isolation_forest: {
        n_estimators: 100,
        contamination: 0.15,
        n_jobs: -1
      },
      one_class_svm: {
        nu: 0.05,
        kernel: 'rbf',
        gamma: 'auto'
      }
    });
    const validationErrors = ref({
      isolation_forest: {},
      one_class_svm: {}
    });

    const canTrain = computed(() => {
      return collectedSamples.value >= minSamples.value;
    });

    const startConsuming = async () => {
      try {
        const response = await mlTrainingApi.post('/ml/start_consuming');
        if (response.data.status === 'Started') {
          loadConsumerStatus();
        }
      } catch (error) {
        console.error('Error starting consumer:', error);
        error.value = t('mlTraining.errors.startConsumingFailed');
      }
    };

    const stopConsuming = async () => {
      try {
        const response = await mlTrainingApi.post('/ml/stop_consuming');
        if (response.data.status === 'Stopped') {
          loadConsumerStatus();
        }
      } catch (error) {
        console.error('Error stopping consumer:', error);
        error.value = t('mlTraining.errors.stopConsumingFailed');
      }
    };

    const loadConsumerStatus = async () => {
      try {
        const response = await mlTrainingApi.get('/ml/consumer_status');
        consumerStatus.value = response.data.status;
      } catch (error) {
        console.error('Error loading consumer status:', error);
        error.value = t('mlTraining.errors.statusLoadFailed');
      }
    };

    const startTraining = async () => {
      try {
        const response = await mlTrainingApi.post('/ml/train');
        if (response.data.status === 'Started') {
          loadTrainingStatus();
        }
      } catch (error) {
        console.error('Error starting training:', error);
        error.value = t('mlTraining.errors.startTrainingFailed');
      }
    };

    const loadTrainingStatus = async () => {
      try {
        const response = await mlTrainingApi.get('/ml/status');
        trainingStatus.value = response.data.training_status;
        collectedSamples.value = response.data.collected_samples;
        minSamples.value = response.data.min_samples_for_training;
      } catch (error) {
        console.error('Error loading training status:', error);
        error.value = t('mlTraining.errors.statusLoadFailed');
      }
    };

    const loadCurrentSettings = async () => {
      try {
        const response = await mlTrainingApi.get('/ml/current_hyperparameters');
        modelSettings.value = response.data;
      } catch (error) {
        console.error('Error loading model settings:', error);
        error.value = t('mlTraining.errors.settingsLoadFailed');
      }
    };

    const updateMinSamples = async () => {
      try {
        const response = await mlTrainingApi.post('/ml/set_min_samples', null, {
          params: { min_samples: minSamplesInput.value }
        });
        if (response.data.status === 'Updated') {
          loadTrainingStatus();
        }
      } catch (error) {
        console.error('Error updating min samples:', error);
        error.value = t('mlTraining.errors.settingsUpdateFailed');
      }
    };

    const openUpdateModal = (model) => {
      currentModel.value = model;
      tempParams.value = JSON.parse(JSON.stringify(modelSettings.value.hyperparameters));
      showUpdateModal.value = true;
    };

    const closeUpdateModal = () => {
      showUpdateModal.value = false;
      currentModel.value = '';
      validationErrors.value = {
        isolation_forest: {},
        one_class_svm: {}
      };
    };

    const updateHyperparameters = async () => {
      try {
        const response = await mlTrainingApi.post('/ml/update_hyperparameters', {
          [currentModel.value]: tempParams.value[currentModel.value]
        });
        if (response.data.status === 'Updated') {
          await loadCurrentSettings();
          closeUpdateModal();
        }
      } catch (error) {
        console.error('Error updating hyperparameters:', error);
        error.value = t('mlTraining.errors.settingsUpdateFailed');
      }
    };

    const downloadModels = async () => {
      try {
        const response = await mlTrainingApi.get('/ml/download_models/', { responseType: 'blob' });
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', 'models.joblib');
        document.body.appendChild(link);
        link.click();
        link.remove();
      } catch (error) {
        console.error('Error downloading models:', error);
        error.value = t('mlTraining.errors.modelDownloadFailed');
      }
    };

    const triggerModelUpload = () => {
      modelInput.value.click();
    };

    const handleModelUpload = async (event) => {
      const file = event.target.files[0];
      if (!file) return;

      const formData = new FormData();
      formData.append('file', file);

      try {
        const response = await mlTrainingApi.post('/ml/upload_models/', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });
        if (response.data.status === 'Uploaded') {
          loadTrainingStatus();
        }
      } catch (error) {
        console.error('Error uploading models:', error);
        error.value = t('mlTraining.errors.modelUploadFailed');
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
      loadTrainingStatus();
      loadCurrentSettings();
    });

    return {
      consumerStatus,
      trainingStatus,
      collectedSamples,
      minSamples,
      minSamplesInput,
      modelInput,
      modelSettings,
      showUpdateModal,
      currentModel,
      tempParams,
      validationErrors,
      canTrain,
      startConsuming,
      stopConsuming,
      loadConsumerStatus,
      startTraining,
      loadTrainingStatus,
      loadCurrentSettings,
      updateMinSamples,
      openUpdateModal,
      closeUpdateModal,
      updateHyperparameters,
      downloadModels,
      triggerModelUpload,
      handleModelUpload,
      statusClass
    };
  }
};
</script>

<style scoped>
.ml-training-view {
  padding: 20px;
}

.control-panel {
  background-color: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.consumer-section, .training-section, .model-settings-section, .model-section {
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

.model-settings-section {
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #eee;
}

.model-card {
  background-color: white;
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.model-card h4 {
  color: #2c3e50;
  margin: 0 0 10px 0;
  font-size: 1.2em;
}

.model-description {
  color: #7f8c8d;
  font-size: 0.9em;
  margin-bottom: 15px;
  font-style: italic;
}

.hyperparameter-display {
  background-color: #f8f9fa;
  padding: 15px;
  border-radius: 6px;
  border: 1px solid #e0e0e0;
}

.param-row {
  display: grid;
  grid-template-columns: 150px 100px 1fr;
  gap: 10px;
  padding: 8px 0;
  border-bottom: 1px solid #eee;
}

.param-row:last-child {
  border-bottom: none;
}

.param-name {
  font-weight: 600;
  color: #2c3e50;
}

.param-value {
  font-family: monospace;
  color: #3498db;
  font-weight: 500;
}

.param-description {
  color: #7f8c8d;
  font-size: 0.9em;
}

.model-section {
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #eee;
}

.model-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.update-button {
  background-color: #3498db;
  color: white;
  border: none;
  padding: 8px 15px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9em;
  transition: background-color 0.3s;
}

.update-button:hover {
  background-color: #2980b9;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background-color: white;
  border-radius: 8px;
  width: 500px;
  max-width: 90%;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.modal-header {
  padding: 15px 20px;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 {
  margin: 0;
  color: #2c3e50;
}

.close-button {
  background: none;
  border: none;
  font-size: 1.5em;
  cursor: pointer;
  color: #7f8c8d;
}

.modal-body {
  padding: 20px;
}

.parameter-inputs {
  display: flex;
  flex-direction: column;
  gap: 15px;
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

.input-group input,
.input-group select {
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1em;
}

.modal-footer {
  padding: 15px 20px;
  border-top: 1px solid #eee;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.cancel-button,
.save-button {
  padding: 8px 20px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1em;
}

.cancel-button {
  background-color: #95a5a6;
  color: white;
  border: none;
}

.save-button {
  background-color: #2ecc71;
  color: white;
  border: none;
}

.cancel-button:hover {
  background-color: #7f8c8d;
}

.save-button:hover {
  background-color: #27ae60;
}

.error-message {
  color: #e74c3c;
  font-size: 0.9em;
  margin-top: 5px;
  padding: 5px;
  background-color: rgba(231, 76, 60, 0.1);
  border-radius: 4px;
  border-left: 3px solid #e74c3c;
}

.status-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.refresh-button {
  padding: 5px 10px;
  background-color: #2ecc71;
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

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
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
</style> 