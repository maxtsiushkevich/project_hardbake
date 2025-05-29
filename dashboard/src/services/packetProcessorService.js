import { packetProcessorApi } from './api';

export const packetProcessorService = {
  async uploadPcapFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await packetProcessorApi.post('/pcap/upload-pcap', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    return response.data;
  },

  async getAllUploads(startPos = null, quantity = null) {
    const params = {};
    if (startPos !== null) params.start_pos = startPos;
    if (quantity !== null) params.quantity = quantity;

    const response = await packetProcessorApi.get('/pcap/all', { params });
    return response.data;
  },

  async getSniffsByStatus(targetStatus) {
    const response = await packetProcessorApi.get('/pcap/status/Running', {
      params: { target_status: targetStatus }
    });
    return response.data;
  },

  async getUploadStatus(uploadId) {
    const response = await packetProcessorApi.get(`/pcap/status/${uploadId}`);
    return response.data;
  },

  async sendStreamsToRmq(uploadId) {
    const response = await packetProcessorApi.post(`/pcap/send/${uploadId}`);
    return response.data;
  },

  async getSendStatus(uploadId) {
    const response = await packetProcessorApi.get(`/pcap/send/${uploadId}`);
    return response.data;
  },

  async getStreams(uploadId) {
    const response = await packetProcessorApi.get(`/pcap/${uploadId}/streams`);
    return response.data;
  },

  async startConsumer(udpTimeout = 10) {
    const response = await packetProcessorApi.post('/management/start', null, {
      params: { udp_timeout: udpTimeout }
    });
    return response.data;
  },

  async stopConsumer() {
    const response = await packetProcessorApi.post('/management/stop');
    return response.data;
  },

  async getConsumerStatus() {
    const response = await packetProcessorApi.get('/management/status');
    return response.data;
  },

  async clearCache() {
    const response = await packetProcessorApi.post('/pcap/clear_cache');
    return response.data;
  }
}; 