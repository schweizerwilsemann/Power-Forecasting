<template>
  <div class="app">
    <!-- Navigation -->
    <nav class="navbar">
      <div class="navbar-brand">
        <h1>PV Power Forecasting</h1>
      </div>
      <div class="navbar-nav">
        <button 
          v-for="tab in tabs" 
          :key="tab.id"
          :class="['nav-item', { active: activeTab === tab.id }]"
          @click="navigate(tab.id)"
        >
          <i :class="tab.icon"></i>
          {{ tab.name }}
        </button>
      </div>
      <div class="navbar-actions">
        <button class="btn btn-sm btn-secondary" @click="refreshAll">
          <i class="icon-refresh"></i>
          Refresh
        </button>
      </div>
    </nav>

    <!-- Main Content -->
    <main class="main-content">
      <!-- Dashboard Tab -->
<Dashboard v-if="activeTab === 'dashboard'" :available-horizons="availableHorizonOptions" />

      <!-- Basic Forecast Tab -->
      <div v-else-if="activeTab === 'forecast'" class="page">
        <header class="hero hero--light">
          <div class="hero__glow"></div>
          <div class="hero__content">
            <p class="eyebrow">Solar intelligence • FastAPI backend</p>
            <h1>PV Power Forecasting</h1>
            <p>Blend weather signals with LightGBM to preview the next energy windows in minutes.</p>
            <div class="hero__chips">
              <span 
                v-if="lastRunLabel" 
                class="chip chip--status"
              >
                {{ lastRunLabel }}
              </span>
              <span 
                v-if="metrics" 
                class="chip chip--accent chip--performance"
              >
                Accuracy band · MAE {{ formattedMae }} · RMSE {{ formattedRmse }}
              </span>
            </div>
          </div>
          <div class="hero__visual" aria-hidden="true">
            <div class="orb orb--one"></div>
            <div class="orb orb--two"></div>
            <div class="orb orb--three"></div>
          </div>
        </header>

        <section
          v-if="metrics"
          class="card-grid metrics-grid metrics-grid--light"
        >
          <article class="metric-card metric-card--light">
            <span>Forecast horizon</span>
            <strong>{{ metrics.horizon }} × 15 min</strong>
            <p>Short-term window balanced for solar ramps.</p>
          </article>
          <article class="metric-card metric-card--light">
            <span>MAE</span>
            <strong>{{ formattedMae }} Wh</strong>
            <p>Average absolute deviation vs. live telemetry.</p>
          </article>
          <article class="metric-card metric-card--light">
            <span>RMSE</span>
            <strong>{{ formattedRmse }} Wh</strong>
            <p>Highlights larger spikes the model still sees.</p>
          </article>
        </section>

        <div class="layout-grid">
          <div class="stack">
            <ForecastForm
              :loading="loading"
              :horizon-options="availableHorizonOptions"
              @forecast="triggerForecast"
            />
            <ForecastInsights :series="results" :metrics="metrics" />
          </div>
          <div class="stack">
            <ForecastChart :series="results" downloadable @download="downloadCsv" />
            <ForecastTimeline :series="results" />
            <ForecastHistory :history="history" @restore="restoreHistory" />
          </div>
        </div>
      </div>

      <!-- Advanced Forecast Tab -->
      <AdvancedForecast
        v-else-if="activeTab === 'advanced'"
        :available-horizons="availableHorizonOptions"
      />

      <!-- Data Quality Tab -->
      <DataQuality v-else-if="activeTab === 'quality'" />

      <!-- Historical Analysis Tab -->
      <HistoricalAnalysis v-else-if="activeTab === 'analysis'" />

      <!-- Model Management Tab -->
      <ModelManagement v-else-if="activeTab === 'models'" />
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import Dashboard from './components/Dashboard.vue';
import ForecastChart from './components/ForecastChart.vue';
import ForecastForm from './components/ForecastForm.vue';
import ForecastHistory from './components/ForecastHistory.vue';
import ForecastInsights from './components/ForecastInsights.vue';
import ForecastTimeline from './components/ForecastTimeline.vue';
import AdvancedForecast from './components/AdvancedForecast.vue';
import DataQuality from './components/DataQuality.vue';
import HistoricalAnalysis from './components/HistoricalAnalysis.vue';
import ModelManagement from './components/ModelManagement.vue';
import { useForecastApi } from './composables/useForecastApi';
import { normalizeTimestamp, toIsoLocalString } from './utils/time';

const MAX_HISTORY = 5;

// Tab management
const router = useRouter();
const route = useRoute();
const activeTab = computed(() => route.name ?? 'dashboard');
const tabs = ref([
  { id: 'dashboard', name: 'Dashboard', icon: 'icon-dashboard' },
  { id: 'forecast', name: 'Basic Forecast', icon: 'icon-chart' },
  { id: 'advanced', name: 'Advanced Forecast', icon: 'icon-target' },
  { id: 'quality', name: 'Data Quality', icon: 'icon-shield' },
  { id: 'analysis', name: 'Historical Analysis', icon: 'icon-trending' },
  { id: 'models', name: 'Model Management', icon: 'icon-cpu' }
]);

const results = ref([]);
const history = ref([]);
const loading = ref(false);
const metrics = ref(null);
const { fetchNext, fetchBatch, fetchMetrics } = useForecastApi();
const availableHorizonOptions = computed(() => {
  const list = metrics.value?.available_horizons;
  if (Array.isArray(list) && list.length) {
    return [...new Set(list)].sort((a, b) => a - b);
  }
  if (metrics.value?.horizon) {
    return [metrics.value.horizon];
  }
  return [1];
});

const deepClone = (data) => JSON.parse(JSON.stringify(data ?? []));

const summarizeSeries = (series) => {
  const values = series
    .map((point) => Number(point?.prediction_wh))
    .filter((value) => Number.isFinite(value));
  if (!values.length) return null;
  const max = Math.max(...values);
  const min = Math.min(...values);
  const avg = values.reduce((sum, value) => sum + value, 0) / values.length;
  const total = values.reduce((sum, value) => sum + value, 0);
  return { max, min, avg, total };
};

const formatRangeLabel = (series) => {
  if (!series.length) return null;
  const first = series[0]?.timestamp ?? 'Step 1';
  const last = series[series.length - 1]?.timestamp ?? `Step ${series.length}`;
  return {
    start: normalizeTimestamp(first) ?? first,
    end: normalizeTimestamp(last) ?? last,
  };
};

const registerHistory = (mode, payload, series) => {
  const stats = summarizeSeries(series);
  if (!stats) return;
  const entry = {
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
    mode,
    modeLabel: mode === 'next' ? 'Immediate horizon' : 'Batch weather',
    steps: series.length,
    createdAt: new Date().toISOString(),
    stats,
    range: formatRangeLabel(series),
    meta: {
      horizon: payload?.horizon ?? series.length,
    },
    series: deepClone(series),
  };
  history.value = [entry, ...history.value].slice(0, MAX_HISTORY);
};

const normalizeSeriesTimestamps = (series) =>
  series.map((point) => ({
    ...point,
    timestamp: point.timestamp ? normalizeTimestamp(point.timestamp) : undefined,
  }));

const triggerForecast = async ({ mode, payload }) => {
  loading.value = true;
  try {
    const response = mode === 'next' ? await fetchNext(payload) : await fetchBatch(payload);
    const normalized = Array.isArray(response) ? response : [response];
    const withIsoTimestamps = normalizeSeriesTimestamps(normalized);
    results.value = withIsoTimestamps;
    registerHistory(mode, payload, withIsoTimestamps);
  } catch (error) {
    alert(error?.response?.data?.detail ?? error.message ?? 'Request failed');
  } finally {
    loading.value = false;
  }
};

const restoreHistory = (entryId) => {
  const entry = history.value.find((item) => item.id === entryId);
  if (!entry) return;
  results.value = deepClone(entry.series);
};

const refreshAll = async () => {
  try {
    metrics.value = await fetchMetrics();
  } catch (error) {
    console.warn('Unable to load metrics', error);
  }
};

const buildCsv = (series) => {
  const header = ['timestamp', 'prediction_wh', 'horizon_steps', 'leaf_indices'];
  const rows = series.map((point) => [
    point.timestamp ?? '',
    Number.isFinite(point.prediction_wh) ? point.prediction_wh : '',
    point.horizon_steps ?? '',
    point.leaf_indices ? JSON.stringify(point.leaf_indices) : '',
  ]);
  return [header, ...rows]
    .map((row) => row.map((cell) => `"${String(cell ?? '').replace(/"/g, '""')}"`).join(','))
    .join('\r\n');
};

const downloadCsv = () => {
  if (!results.value.length) return;
  const csv = buildCsv(results.value);
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = `pv-forecast-${toIsoLocalString(new Date()).replace(/[:]/g, '-')}.csv`;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  URL.revokeObjectURL(url);
};

const lastRunLabel = computed(() => {
  if (!results.value.length) return null;
  const lastPoint = results.value[results.value.length - 1];
  if (!lastPoint?.timestamp) return `Generated ${results.value.length} step(s)`;
  return `Latest timestamp: ${normalizeTimestamp(lastPoint.timestamp) ?? lastPoint.timestamp}`;
});

const formattedMae = computed(() =>
  metrics.value?.mae != null ? metrics.value.mae.toFixed(1) : '–',
);

const formattedRmse = computed(() =>
  metrics.value?.rmse != null ? metrics.value.rmse.toFixed(1) : '–',
);

const navigate = (tabId) => {
  if (tabId !== route.name) {
    router.push({ name: tabId });
  }
};

onMounted(async () => {
  await refreshAll();
});
</script>

<style scoped src="./styles/app.css"></style>
