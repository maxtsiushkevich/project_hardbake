import axios from 'axios';
import router from '../router';
import { serviceHosts } from '../config/hosts';

const API_BASE_URLS = {
  auth: `${serviceHosts.auth}`,
  sniffer: `${serviceHosts.sniffer}`,
  systemInfo: `${serviceHosts.systemInfo}`,
  packetProcessor: `${serviceHosts.packetProcessor}`,
  mlDataProcessor: `${serviceHosts.mlDataProcessor}`,
  mlTraining: `${serviceHosts.mlTraining}`,
  notification: `${serviceHosts.notification}`,
  threatDetection: `${serviceHosts.threatDetection}`
};

const getToken = () => {
  const cookies = document.cookie.split(';')
  const tokenCookie = cookies.find(cookie => cookie.trim().startsWith('access_token='))
  return tokenCookie ? tokenCookie.split('=')[1] : null
}

const removeToken = () => {
  document.cookie = 'access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:01 GMT'
}

const createApiClient = (baseURL) => {
  const client = axios.create({
    baseURL,
    headers: {
      'Content-Type': 'application/json'
    },
    withCredentials: true
  });

  // Add request interceptor to add token to all requests
  client.interceptors.request.use(config => {
    const token = getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  })

  // Add response interceptor to handle token expiration
  client.interceptors.response.use(
    response => response,
    error => {
      if (error.response?.status === 401) {
        removeToken()
        router.push('/login')
      }
      return Promise.reject(error)
    }
  )

  return client;
};

export const authApi = createApiClient(API_BASE_URLS.auth);
export const snifferApi = createApiClient(API_BASE_URLS.sniffer);
export const systemInfoApi = createApiClient(API_BASE_URLS.systemInfo);
export const packetProcessorApi = createApiClient(API_BASE_URLS.packetProcessor);
export const mlDataProcessorApi = createApiClient(API_BASE_URLS.mlDataProcessor);
export const mlTrainingApi = createApiClient(API_BASE_URLS.mlTraining);
export const notificationApi = createApiClient(API_BASE_URLS.notification);
export const threatDetectionApi = createApiClient(API_BASE_URLS.threatDetection); 