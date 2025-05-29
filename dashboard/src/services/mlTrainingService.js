import { mlTrainingApi } from './api';

export const mlTrainingService = {
  async startConsuming() {
    const response = await mlTrainingApi.post('/ml/start_consuming');
    return response.data;
  },

  async stopConsuming() {
    const response = await mlTrainingApi.post('/ml/stop_consuming');
    return response.data;
  },

  async startTraining() {
    const response = await mlTrainingApi.post('/ml/train');
    return response.data;
  },

  async setMinSamples(minSamples) {
    const response = await mlTrainingApi.post('/ml/set_min_samples', null, {
      params: { min_samples: minSamples }
    });
    return response.data;
  },

  async getStatus() {
    const response = await mlTrainingApi.get('/ml/status');
    return response.data;
  },

  async getCurrentSettings() {
    const response = await mlTrainingApi.get('/ml/current_settings');
    return response.data;
  },

  async getConsumerStatus() {
    const response = await mlTrainingApi.get('/ml/consumer_status');
    return response.data;
  },

  async downloadModels() {
    const response = await mlTrainingApi.get('/ml/download_models/', {
      responseType: 'blob'
    });
    return response.data;
  },

  async uploadModels(file) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await mlTrainingApi.post('/ml/upload_models/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    return response.data;
  },

  async updateHyperparameters(hyperparameters) {
    const response = await mlTrainingApi.post('/ml/update_hyperparameters', hyperparameters);
    return response.data;
  }
}; 