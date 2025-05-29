<template>
  <div class="about">
    <h1>{{ $t('about.title') }}</h1>
    
    <section class="overview">
      <h2>{{ $t('about.overview.title') }}</h2>
      <p>{{ $t('about.overview.description') }}</p>
    </section>

    <section class="features">
      <h2>{{ $t('about.features.title') }}</h2>
      <ul>
        <li>{{ $t('about.features.items.sniffing') }}</li>
        <li>{{ $t('about.features.items.systemInfo') }}</li>
        <li>{{ $t('about.features.items.packetProcessing') }}</li>
        <li>{{ $t('about.features.items.mlProcessing') }}</li>
        <li>{{ $t('about.features.items.mlTraining') }}</li>
        <li>{{ $t('about.features.items.threatDetection') }}</li>
      </ul>
    </section>

    <section class="tech-stack">
      <h2>{{ $t('about.techStack.title') }}</h2>
      <p>{{ $t('about.techStack.description') }}</p>
    </section>

    <section class="services">
      <h2>{{ $t('about.services.title') }}</h2>
      <div class="services-grid">
        <div class="service-card" v-for="(service, index) in services" :key="index">
          <h3>{{ $t(`about.services.items.${service.id}`) }}</h3>
          <div class="service-info">
            <span class="port">{{ $t('about.services.port') }}: {{ service.port }}</span>
            <span class="status" :class="service.status">
              {{ $t(`about.services.status.${service.status}`) }}
            </span>
          </div>
        </div>
      </div>
      <button @click="checkServices" class="refresh-btn">
        {{ $t('about.services.refresh') }}
      </button>
    </section>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const services = ref([
  { id: 'sniffer', port: 5000, status: 'running' },
  { id: 'systemInfo', port: 5001, status: 'running' },
  { id: 'packetProcessor', port: 5002, status: 'running' },
  { id: 'mlDataProcessor', port: 5003, status: 'running' },
  { id: 'mlTraining', port: 5004, status: 'running' },
  { id: 'threatDetection', port: 5005, status: 'running' }
])

const checkServices = () => {
  services.value.forEach(service => {
    service.status = 'checking'
    // Simulate service check
    setTimeout(() => {
      service.status = Math.random() > 0.2 ? 'running' : 'notAvailable'
    }, 1000)
  })
}
</script>

<style scoped>
.about {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

section {
  margin-bottom: 3rem;
}

h1 {
  font-size: 2.5rem;
  margin-bottom: 2rem;
  color: #2c3e50;
}

h2 {
  font-size: 1.8rem;
  margin-bottom: 1rem;
  color: #2c3e50;
}

h3 {
  font-size: 1.2rem;
  margin-bottom: 0.5rem;
  color: #2c3e50;
}

p {
  line-height: 1.6;
  color: #666;
}

.features ul {
  list-style: none;
  padding: 0;
}

.features li {
  margin-bottom: 0.5rem;
  padding-left: 1.5rem;
  position: relative;
}

.features li::before {
  content: "•";
  position: absolute;
  left: 0;
  color: #42b983;
}

.services-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.service-card {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.service-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 1rem;
}

.port {
  color: #666;
  font-size: 0.9rem;
}

.status {
  padding: 0.25rem 0.75rem;
  border-radius: 4px;
  font-size: 0.9rem;
}

.status.running {
  background: #e8f5e9;
  color: #2e7d32;
}

.status.notAvailable {
  background: #ffebee;
  color: #c62828;
}

.status.checking {
  background: #fff3e0;
  color: #ef6c00;
}

.refresh-btn {
  background: #2ecc71;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
  transition: background-color 0.3s;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.refresh-btn:hover {
  background: #27ae60;
}

.refresh-btn::before {
  content: "↻";
  font-size: 1.2em;
  transition: transform 0.3s;
}

.refresh-btn:hover::before {
  transform: rotate(180deg);
}
</style>
