import { mlDataProcessorApi } from './api';

export const mlDataProcessorService = {
  async startConsumer() {
    const response = await mlDataProcessorApi.post('/management/start');
    return response.data;
  },

  async stopConsumer() {
    const response = await mlDataProcessorApi.post('/management/stop');
    return response.data;
  },

  async getConsumerStatus() {
    const response = await mlDataProcessorApi.get('/management/status');
    return response.data;
  },

  async getProcessingStats() {
    const response = await mlDataProcessorApi.get('/stats');
    return response.data;
  }
}; 