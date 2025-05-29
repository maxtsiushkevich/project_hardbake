const hosts = {
  development: {
    auth: 'http://localhost:8008',
    sniffer: 'http://localhost:8000',
    systemInfo: 'http://localhost:8001',
    packetProcessor: 'http://localhost:8002',
    mlDataProcessor: 'http://localhost:8003',
    mlTraining: 'http://localhost:8004',
    threatDetection: 'http://localhost:8005',
    notification: 'http://localhost:8006',
    grafana: 'http://localhost:3000'
  },
  production: {
    auth: 'http://auth-svc:8008',
    sniffer: 'http://localhost:8000',
    systemInfo: 'http://localhost:8001',
    packetProcessor: 'http://packet-processor-svc:8002',
    mlDataProcessor: 'http://ml-data-processor-svc:8003',
    mlTraining: 'http://ml-training-svc:8004',
    threatDetection: 'http://threat-detection-svc:8005',
    notification: 'http://notification-svc:8006',
    grafana: 'http://grafana:3000'
  }
}

// Get the current environment from Vite's environment variables
const currentEnv = import.meta.env.MODE || 'development'

// Export the hosts for the current environment
export const serviceHosts = hosts[currentEnv]

// Export all environments for reference
export const allHosts = hosts

// Helper function to get a specific service URL
export const getServiceUrl = (serviceName) => {
  return serviceHosts[serviceName]
} 