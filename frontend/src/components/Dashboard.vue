<style scoped src="../styles/components/Dashboard.css"></style>

<template>
  <div class="dashboard">
    <!-- Header Section -->
    <header class="dashboard-header">
      <div class="header-content">
        <h1>PV Power Forecasting Dashboard</h1>
        <div class="header-actions">
          <button class="btn btn-primary" @click="refreshData">
            <i class="icon-refresh"></i>
            Refresh
          </button>
          <div class="status-indicator" :class="systemStatus">
            <span class="status-dot"></span>
            {{ systemStatusText }}
          </div>
        </div>
      </div>
    </header>

    <!-- Key Metrics Grid -->
    <section class="metrics-grid">
      <div class="metric-card">
        <div class="metric-header">
          <h3>System Health</h3>
          <span class="metric-value" :class="healthStatus">{{ healthScore }}%</span>
        </div>
        <div class="metric-details">
          <div class="detail-item">
            <span>Model Status</span>
            <span :class="modelStatus ? 'status-good' : 'status-bad'">
              {{ modelStatus ? 'Loaded' : 'Not Loaded' }}
            </span>
          </div>
          <div class="detail-item">
            <span>Uptime</span>
            <span>{{ formatUptime(uptime) }}</span>
          </div>
        </div>
      </div>

      <div class="metric-card">
        <div class="metric-header">
          <h3>Data Quality</h3>
          <span class="metric-value" :class="qualityStatus">{{ dataQuality }}%</span>
        </div>
        <div class="metric-details">
          <div class="detail-item">
            <span>Completeness</span>
            <span>{{ dataCompleteness }}%</span>
          </div>
          <div class="detail-item">
            <span>Anomalies</span>
            <span>{{ anomalyCount }}</span>
          </div>
        </div>
      </div>

      <div class="metric-card">
        <div class="metric-header">
          <h3>Forecast Accuracy</h3>
          <span class="metric-value">{{ accuracy }}%</span>
        </div>
        <div class="metric-details">
          <div class="detail-item">
            <span>MAE</span>
            <span>{{ mae }} Wh</span>
          </div>
          <div class="detail-item">
            <span>RMSE</span>
            <span>{{ rmse }} Wh</span>
          </div>
        </div>
      </div>

      <div class="metric-card">
        <div class="metric-header">
          <h3>Performance</h3>
          <span class="metric-value">{{ cpuUsage }}%</span>
        </div>
        <div class="metric-details">
          <div class="detail-item">
            <span>CPU Usage</span>
            <span>{{ cpuUsage }}%</span>
          </div>
          <div class="detail-item">
            <span>Memory</span>
            <span>{{ memoryUsage }}%</span>
          </div>
        </div>
      </div>
    </section>

    <!-- Main Content Grid -->
    <div class="dashboard-grid">
      <!-- Real-time Chart -->
      <div class="chart-section">
        <div class="section-header">
          <h2>Real-time Forecast</h2>
          <div class="chart-controls">
            <select v-model.number="selectedHorizon">
              <option
                v-for="option in horizonOptions"
                :key="`dashboard-${option}`"
                :value="option"
              >
                {{ describeHorizon(option) }}
              </option>
            </select>
            <button class="btn btn-sm" @click="toggleAutoRefresh">
              {{ autoRefresh ? 'Pause' : 'Auto' }}
            </button>
          </div>
        </div>
        <div class="chart-container">
          <Line :data="chartData" :options="chartOptions" />
        </div>
      </div>

      <!-- System Monitoring -->
      <div class="monitoring-section">
        <div class="section-header">
          <h2>System Monitoring</h2>
          <button class="btn btn-sm" @click="refreshMonitoring">Refresh</button>
        </div>
        <div class="monitoring-content">
          <div class="monitor-item">
            <div class="monitor-label">CPU Usage</div>
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: cpuUsage + '%' }"></div>
            </div>
            <div class="monitor-value">{{ cpuUsage }}%</div>
          </div>
          <div class="monitor-item">
            <div class="monitor-label">Memory Usage</div>
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: memoryUsage + '%' }"></div>
            </div>
            <div class="monitor-value">{{ memoryUsage }}%</div>
          </div>
          <div class="monitor-item">
            <div class="monitor-label">Disk Usage</div>
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: diskUsage + '%' }"></div>
            </div>
            <div class="monitor-value">{{ diskUsage }}%</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Advanced Features Section -->
    <section class="advanced-features">
      <div class="section-header">
        <h2>Advanced Features</h2>
      </div>
      <div class="features-grid">
        <div class="feature-card" @click="openAdvancedForecast">
          <div class="feature-icon">🎯</div>
          <h3>Advanced Forecast</h3>
          <p>Confidence intervals, ensemble models, multiple scenarios</p>
        </div>
        <div class="feature-card" @click="openDataQuality">
          <div class="feature-icon">📊</div>
          <h3>Data Quality</h3>
          <p>Anomaly detection, data validation, quality metrics</p>
        </div>
        <div class="feature-card" @click="openHistoricalAnalysis">
          <div class="feature-icon">📈</div>
          <h3>Historical Analysis</h3>
          <p>Performance trends, accuracy analysis, model comparison</p>
        </div>
        <div class="feature-card" @click="openModelManagement">
          <div class="feature-icon">🤖</div>
          <h3>Model Management</h3>
          <p>Model training, versioning, performance monitoring</p>
        </div>
      </div>
    </section>

    <!-- Alerts Section -->
    <section v-if="alerts.length > 0" class="alerts-section">
      <div class="section-header">
        <h2>System Alerts</h2>
        <button class="btn btn-sm" @click="clearAlerts">Clear All</button>
      </div>
      <div class="alerts-list">
        <div 
          v-for="alert in alerts" 
          :key="alert.id" 
          class="alert-item" 
          :class="alert.severity"
        >
          <div class="alert-content">
            <div class="alert-title">{{ alert.title }}</div>
            <div class="alert-message">{{ alert.message }}</div>
            <div class="alert-time">{{ formatTime(alert.timestamp) }}</div>
          </div>
          <button class="alert-close" @click="dismissAlert(alert.id)">×</button>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import { Line } from 'vue-chartjs';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { toIsoLocalString } from '../utils/time';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

const props = defineProps({
  availableHorizons: {
    type: Array,
    default: () => [],
  },
});

// Reactive data
const systemStatus = ref('healthy');
const healthScore = ref(95);
const modelStatus = ref(true);
const uptime = ref(0);
const dataQuality = ref(92);
const dataCompleteness = ref(98);
const anomalyCount = ref(3);
const accuracy = ref(87);
const mae = ref(45.2);
const rmse = ref(67.8);
const cpuUsage = ref(25);
const memoryUsage = ref(68);
const diskUsage = ref(45);
const selectedHorizon = ref(1);
const autoRefresh = ref(true);
const alerts = ref([]);
const horizonOptions = computed(() => {
  const base = Array.isArray(props.availableHorizons) ? props.availableHorizons : [];
  const filtered = base.filter((value) => Number.isInteger(value) && value > 0);
  if (filtered.length) {
    return [...new Set(filtered)].sort((a, b) => a - b);
  }
  return [1];
});
const describeHorizon = (value) => {
  const minutes = value * 15;
  if (minutes % 60 === 0) {
    const hours = minutes / 60;
    return `${value} Step${value > 1 ? 's' : ''} (${hours}hr${hours > 1 ? 's' : ''})`;
  }
  return `${value} Step${value > 1 ? 's' : ''} (${minutes}min)`;
};

watch(
  horizonOptions,
  (options) => {
    if (!options.includes(selectedHorizon.value)) {
      selectedHorizon.value = options[0];
    }
  },
  { immediate: true },
);

// Chart data
const chartData = ref({
  labels: [],
  datasets: [
    {
      label: 'Predicted (Wh)',
      data: [],
      borderColor: '#3b82f6',
      backgroundColor: 'rgba(59, 130, 246, 0.1)',
      fill: true,
      tension: 0.4,
    },
    {
      label: 'Confidence Upper',
      data: [],
      borderColor: '#10b981',
      backgroundColor: 'rgba(16, 185, 129, 0.1)',
      fill: '+1',
      tension: 0.4,
    },
    {
      label: 'Confidence Lower',
      data: [],
      borderColor: '#10b981',
      backgroundColor: 'rgba(16, 185, 129, 0.1)',
      fill: false,
      tension: 0.4,
    }
  ]
});

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: true,
      position: 'top',
    },
    tooltip: {
      mode: 'index',
      intersect: false,
    }
  },
  scales: {
    x: {
      display: true,
      title: {
        display: true,
        text: 'Time'
      }
    },
    y: {
      display: true,
      title: {
        display: true,
        text: 'Power (Wh)'
      }
    }
  },
  interaction: {
    mode: 'nearest',
    axis: 'x',
    intersect: false
  }
};

// Computed properties
const systemStatusText = computed(() => {
  switch (systemStatus.value) {
    case 'healthy': return 'System Healthy';
    case 'warning': return 'System Warning';
    case 'error': return 'System Error';
    default: return 'Unknown';
  }
});

const healthStatus = computed(() => {
  if (healthScore.value >= 90) return 'status-good';
  if (healthScore.value >= 70) return 'status-warning';
  return 'status-bad';
});

const qualityStatus = computed(() => {
  if (dataQuality.value >= 90) return 'status-good';
  if (dataQuality.value >= 70) return 'status-warning';
  return 'status-bad';
});

// Methods
const refreshData = async () => {
  try {
    // Fetch system health
    const healthResponse = await fetch('/monitoring/health');
    const healthData = await healthResponse.json();
    
    systemStatus.value = healthData.status;
    healthScore.value = healthData.model_loaded ? 95 : 60;
    modelStatus.value = healthData.model_loaded;
    uptime.value = healthData.uptime;
    cpuUsage.value = healthData.cpu_usage;
    memoryUsage.value = healthData.memory_usage.percent;

    // Fetch data quality
    const qualityResponse = await fetch('/data/quality');
    const qualityData = await qualityResponse.json();
    
    dataQuality.value = qualityData.quality_score;
    dataCompleteness.value = qualityData.data_completeness;
    anomalyCount.value = qualityData.anomaly_count;

    // Fetch metrics
    const metricsResponse = await fetch('/metrics');
    const metricsData = await metricsResponse.json();
    
    mae.value = metricsData.mae;
    rmse.value = metricsData.rmse;
    accuracy.value = Number((100 - (metricsData.mae / 1000) * 100).toFixed(3)); // Simplified accuracy calculation, 3 decimals

    // Update forecast
    await updateForecast();
  } catch (error) {
    console.error('Failed to refresh data:', error);
    addAlert('error', 'Data Refresh Failed', 'Unable to fetch latest system data');
  }
};

const updateForecast = async () => {
  try {
    const response = await fetch('/forecast/advanced', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        horizon: selectedHorizon.value,
        include_confidence: true,
        ensemble_mode: false
      })
    });
    
    const data = await response.json();
    
    // Update chart data
    const now = new Date();
    const labels = [];
    const predictions = [];
    const upperBounds = [];
    const lowerBounds = [];
    
    for (let i = 0; i < selectedHorizon.value; i++) {
      const time = new Date(now.getTime() + i * 15 * 60000);
      labels.push(toIsoLocalString(time));
      predictions.push(data.prediction_wh);
      
      if (data.confidence_interval) {
        upperBounds.push(data.confidence_interval.upper);
        lowerBounds.push(data.confidence_interval.lower);
      }
    }
    
    chartData.value = {
      labels,
      datasets: [
        {
          ...chartData.value.datasets[0],
          data: predictions
        },
        {
          ...chartData.value.datasets[1],
          data: upperBounds
        },
        {
          ...chartData.value.datasets[2],
          data: lowerBounds
        }
      ]
    };
  } catch (error) {
    console.error('Failed to update forecast:', error);
    addAlert('error', 'Forecast Update Failed', 'Unable to generate new forecast');
  }
};

watch(selectedHorizon, () => {
  updateForecast();
});

const refreshMonitoring = async () => {
  try {
    const response = await fetch('/monitoring/performance');
    const data = await response.json();
    
    cpuUsage.value = data.system.cpu_percent;
    memoryUsage.value = data.system.memory_percent;
    diskUsage.value = data.system.disk_percent;
  } catch (error) {
    console.error('Failed to refresh monitoring:', error);
  }
};

const toggleAutoRefresh = () => {
  autoRefresh.value = !autoRefresh.value;
};

const addAlert = (severity, title, message) => {
  const alert = {
    id: Date.now(),
    severity,
    title,
    message,
    timestamp: new Date()
  };
  alerts.value.unshift(alert);
  
  // Auto-dismiss after 10 seconds
  setTimeout(() => {
    dismissAlert(alert.id);
  }, 10000);
};

const dismissAlert = (id) => {
  alerts.value = alerts.value.filter(alert => alert.id !== id);
};

const clearAlerts = () => {
  alerts.value = [];
};

const formatUptime = (seconds) => {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  return `${hours}h ${minutes}m`;
};

const formatTime = (timestamp) => {
  return toIsoLocalString(timestamp) || timestamp;
};

// Feature actions
const openAdvancedForecast = () => {
  // Navigate to advanced forecast page
  console.log('Opening advanced forecast');
};

const openDataQuality = () => {
  // Navigate to data quality page
  console.log('Opening data quality');
};

const openHistoricalAnalysis = () => {
  // Navigate to historical analysis page
  console.log('Opening historical analysis');
};

const openModelManagement = () => {
  // Navigate to model management page
  console.log('Opening model management');
};

// Auto-refresh interval
let refreshInterval;

onMounted(() => {
  refreshData();
  
  if (autoRefresh.value) {
    refreshInterval = setInterval(refreshData, 30000); // Refresh every 30 seconds
  }
});

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval);
  }
});
</script>
