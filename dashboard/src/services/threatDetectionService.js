import { threatDetectionApi } from './api';

export const threatDetectionService = {
  async startDetection() {
    const response = await threatDetectionApi.post('/detect/start');
    return response.data;
  },

  async stopDetection() {
    const response = await threatDetectionApi.post('/detect/stop');
    return response.data;
  },

  async getStatus() {
    const response = await threatDetectionApi.get('/detect/status');
    return response.data;
  },

  async setBatchSize(size) {
    const response = await threatDetectionApi.patch('/detect/set_batch_size', null, {
      params: { size }
    });
    return response.data;
  },

  async getBatchSize() {
    const response = await threatDetectionApi.get('/detect/get_batch_size');
    return response.data;
  },

  async uploadModels(file) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await threatDetectionApi.post('/detect/upload_models/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    return response.data;
  },

  async getDetectionStats() {
    const response = await threatDetectionApi.get('/detect/stats');
    return response.data;
  }
}; 