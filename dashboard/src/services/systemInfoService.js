import { systemInfoApi } from './api';

export const systemInfoService = {
  async getInterfaces() {
    const response = await systemInfoApi.get('/interfaces/all');
    return response.data;
  },

  async getInterfaceStats(interfaceName) {
    const response = await systemInfoApi.get(`/interfaces/${interfaceName}/stats`);
    return response.data;
  },

  async getSystemStats() {
    const response = await systemInfoApi.get('/system/stats');
    return response.data;
  }
}; 