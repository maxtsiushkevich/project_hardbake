import { notificationApi } from './api';

class ValidationError extends Error {
  constructor(errors) {
    super('Validation Error');
    this.name = 'ValidationError';
    this.errors = errors;
  }
}

export const notificationService = {
  async startConsuming() {
    try {
      const response = await notificationApi.post(`/notification/start`);
      return response.data;
    } catch (error) {
      if (error.response?.status === 422) {
        throw new ValidationError(error.response.data.detail);
      }
      throw error;
    }
  },

  async stopConsuming() {
    try {
      const response = await notificationApi.post(`/notification/stop`);
      return response.data;
    } catch (error) {
      if (error.response?.status === 422) {
        throw new ValidationError(error.response.data.detail);
      }
      throw error;
    }
  },

  async getStatus() {
    try {
      const response = await notificationApi.get(`/notification/status`);
      return response.data;
    } catch (error) {
      if (error.response?.status === 422) {
        throw new ValidationError(error.response.data.detail);
      }
      throw error;
    }
  },

  async getMetaList(params = {}) {
    try {
      const response = await notificationApi.get(`/metadata/`, { params });
      return response.data;
    } catch (error) {
      if (error.response?.status === 422) {
        throw new ValidationError(error.response.data.detail);
      }
      throw error;
    }
  },

  async getMetaWithFeatures(metaId) {
    try {
      const response = await notificationApi.get(`/metadata/${metaId}`);
      return response.data;
    } catch (error) {
      if (error.response?.status === 422) {
        throw new ValidationError(error.response.data.detail);
      }
      throw error;
    }
  },

  async getStatistics() {
    try {
      const response = await notificationApi.get(`/metadata/statistics`);
      return response.data;
    } catch (error) {
      if (error.response?.status === 422) {
        throw new ValidationError(error.response.data.detail);
      }
      throw error;
    }
  }
}; 