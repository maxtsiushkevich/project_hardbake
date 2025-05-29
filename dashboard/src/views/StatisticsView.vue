<template>
  <div class="statistics-view">
    <h2>{{ $t('nav.statistics') }}</h2>
    <div class="charts-container">
      <div class="grafana-container">
        <iframe 
          src="http://localhost:3000/d-solo/cekkes52gb3swd/project-hardbake-dashboard?orgId=1&timezone=browser&panelId=1&__feature.dashboardSceneSolo" 
          class="grafana-frame"
        ></iframe>
      </div>
      <div class="grafana-container">
        <iframe 
          src="http://localhost:3000/d-solo/cekkes52gb3swd/project-hardbake-dashboard?orgId=1&timezone=browser&panelId=2&__feature.dashboardSceneSolo"
          class="grafana-frame"
        ></iframe>
      </div>
      <div class="grafana-container">
        <iframe 
          src="http://localhost:3000/d-solo/cekkes52gb3swd/project-hardbake-dashboard?orgId=1&timezone=browser&panelId=3&__feature.dashboardSceneSolo"
          class="grafana-frame"
        ></iframe>
      </div>
      <div class="grafana-container">
        <iframe 
          src="http://localhost:3000/d-solo/cekkes52gb3swd/project-hardbake-dashboard?orgId=1&timezone=browser&panelId=4&__feature.dashboardSceneSolo"
          class="grafana-frame"
        ></iframe>
      </div>
      <div class="grafana-container">
        <iframe 
          src="http://localhost:3000/d-solo/cekkes52gb3swd/project-hardbake-dashboard?orgId=1&timezone=browser&panelId=6&__feature.dashboardSceneSolo"
          class="grafana-frame"
        ></iframe>
      </div>
      <div class="grafana-container">
        <iframe 
          src="http://localhost:3000/d-solo/cekkes52gb3swd/project-hardbake-dashboard?orgId=1&timezone=browser&panelId=5&__feature.dashboardSceneSolo"
          class="grafana-frame"
        ></iframe>
      </div>
      <div class="grafana-container">
        <iframe 
          src="http://localhost:3000/d-solo/cekkes52gb3swd/project-hardbake-dashboard?orgId=1&timezone=browser&panelId=7&__feature.dashboardSceneSolo"
          class="grafana-frame"
        ></iframe>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'StatisticsView'
}
</script>

<style scoped>
.statistics-view {
  padding: 20px;
}

.charts-container {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-top: 20px;
}

.grafana-container {
  background-color: white;
  padding: 5px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  aspect-ratio: 16/9;
}

.grafana-frame {
  width: 100%;
  height: 100%;
  border: none;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

@media (max-width: 1600px) {
  .charts-container {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 1024px) {
  .charts-container {
    grid-template-columns: 1fr;
  }
}
</style> 