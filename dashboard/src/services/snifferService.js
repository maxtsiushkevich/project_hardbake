import { snifferApi } from './api';
import { systemInfoApi } from './api';

export const snifferService = {
  async getInterfaces() {
    try {
      const response = await systemInfoApi.get('/interfaces/all');
      // Filter out any null or undefined interfaces and map to names
      return response.data
        .filter(iface => iface && iface.name)
        .map(iface => iface.name);
    } catch (error) {
      console.error('Error loading interfaces:', error);
      return []; // Return empty array if there's an error
    }
  },

  async startSniffing(interfaceName, writeToFile, filter) {
    const response = await snifferApi.post('/sniffer-rmq/start', filter, {
      params: {
        iface: interfaceName,
        write_in_file: writeToFile
      }
    });
    return response.data;
  },

  async stopSniffing(sniffId) {
    const response = await snifferApi.patch('/sniffer-rmq/stop', null, {
      params: { sniff_id: sniffId }
    });
    return response.data;
  },

  async getActiveSessions(startPos = null, quantity = null) {
    const params = {};
    if (startPos !== null) params.start_pos = startPos;
    if (quantity !== null) params.quantity = quantity;
    const response = await snifferApi.get('/sniffer-rmq/all', { params });
    return response.data.sniffs;
  },

  async getSniffsByStatus(targetStatus) {
    const response = await snifferApi.get(`/sniffer-rmq/status/${targetStatus}`);
    return response.data.sniffs;
  },

  async getSniffDetails(taskId) {
    const response = await snifferApi.get(`/sniffer-rmq/${taskId}`);
    return response.data;
  },

  async clearCache() {
    const response = await snifferApi.post('/sniffer-rmq/clear_cache');
    return response.data;
  },

  async getMetrics() {
    const response = await snifferApi.get('/metrics');
    return response.data;
  }
}; 