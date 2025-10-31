<template>
  <div class="historical-analysis">
    <div class="section-header">
      <h2>Historical Analysis</h2>
      <p>Review performance trends and aggregated metrics from previous forecasts</p>
      <p class="date-hint">
        Dữ liệu mẫu hiện có từ <strong>{{ MIN_DATA_DATE }}</strong> đến <strong>{{ MAX_DATA_DATE }}</strong>
      </p>
    </div>

    <form class="analysis-filters" @submit.prevent="runAnalysis">
      <div class="filter-group">
        <label for="start-date">Start date</label>
        <input id="start-date" v-model="startDate" type="date" required />
      </div>
      <div class="filter-group">
        <label for="end-date">End date</label>
        <input id="end-date" v-model="endDate" type="date" required />
      </div>
      <div class="filter-group">
        <label for="aggregation">Aggregation</label>
        <select id="aggregation" v-model="aggregation">
          <option value="hour">Hourly</option>
          <option value="day">Daily</option>
          <option value="week">Weekly</option>
        </select>
      </div>
      <div class="filter-actions">
        <button class="btn btn-primary" type="submit" :disabled="loading">
          <i class="icon-search"></i>
          {{ loading ? 'Analyzing...' : 'Run analysis' }}
        </button>
      </div>
    </form>

    <div v-if="error" class="alert alert-error">
      {{ error }}
    </div>

    <section v-if="analysis" class="analysis-results">
      <div class="card-grid metrics-grid">
        <article
          v-for="metric in metricSummary"
          :key="metric.label"
          class="metric-card"
        >
          <span>{{ metric.label }}</span>
          <strong>{{ metric.value }}</strong>
          <p>{{ metric.description }}</p>
        </article>
      </div>

      <div v-if="trendEntries.length" class="trend-grid">
        <div
          v-for="trend in trendEntries"
          :key="trend.label"
          class="trend-card"
        >
          <span class="trend-label">{{ trend.label }}</span>
          <span class="trend-value">{{ trend.value }}</span>
        </div>
      </div>

      <div class="chart-section">
        <div class="section-header">
          <h3>Performance over time</h3>
          <p>
            {{ formattedPeriod }}
          </p>
        </div>
        <div v-if="hasSeriesData" class="chart-container">
          <Line :data="chartData" :options="chartOptions" />
        </div>
        <div v-else class="empty-state">
          <div class="empty-icon">📈</div>
          <p>No historical data points were returned for the selected window.</p>
        </div>
      </div>

      <div v-if="displayRows.length" class="table-section">
        <div class="section-header">
          <h3>Aggregated breakdown</h3>
          <p>Detailed view of the returned data points</p>
        </div>
        <div class="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Timestamp</th>
                <th v-for="key in valueKeys" :key="key">
                  {{ key }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in displayRows" :key="row.timestamp">
                <td>{{ formatTimestamp(row.timestamp) }}</td>
                <td v-for="key in valueKeys" :key="`${row.timestamp}-${key}`">
                  {{ formatNumber(row[key]) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
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
import { useOperationsApi } from '../composables/useOperationsApi';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

const { fetchHistoricalAnalysis } = useOperationsApi();

const loading = ref(false);
const error = ref('');
const analysis = ref(null);

const MIN_DATA_DATE = '2017-01-01';
const MAX_DATA_DATE = '2022-08-31';
const DEFAULT_WINDOW_DAYS = 30;

const maxDate = new Date(`${MAX_DATA_DATE}T00:00:00`);
const defaultEnd = MAX_DATA_DATE;
const defaultStart = new Date(maxDate.getTime() - DEFAULT_WINDOW_DAYS * 24 * 60 * 60 * 1000)
  .toISOString()
  .slice(0, 10);

const startDate = ref(defaultStart);
const endDate = ref(defaultEnd);
const aggregation = ref('day');

const colorPalette = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#6366f1'];

const metricSummary = computed(() => {
  if (!analysis.value?.metrics) {
    return [];
  }
  return Object.entries(analysis.value.metrics).map(([key, value]) => ({
    label: key.toUpperCase(),
    value: formatNumber(value),
    description: describeMetric(key),
  }));
});

const trendEntries = computed(() => {
  if (!analysis.value?.trends) {
    return [];
  }
  return Object.entries(analysis.value.trends).map(([key, value]) => ({
    label: key.replace(/_/g, ' '),
    value,
  }));
});

const hasSeriesData = computed(
  () => Boolean(analysis.value?.data_points?.length && valueKeys.value.length),
);

const valueKeys = computed(() => {
  const points = analysis.value?.data_points;
  if (!points?.length) {
    return [];
  }
  const sample = points.find((item) => item && typeof item === 'object');
  if (!sample) {
    return [];
  }
  return Object.keys(sample).filter(
    (key) => key !== 'timestamp' && typeof sample[key] === 'number',
  );
});

const chartData = computed(() => {
  if (!hasSeriesData.value) {
    return {
      labels: [],
      datasets: [],
    };
  }
  const labels = analysis.value.data_points.map((point) => formatTimestamp(point.timestamp));
  const datasets = valueKeys.value.map((key, index) => ({
    label: key.toUpperCase(),
    data: analysis.value.data_points.map((point) => point[key]),
    borderColor: colorPalette[index % colorPalette.length],
    backgroundColor: `${colorPalette[index % colorPalette.length]}33`,
    tension: 0.35,
    fill: false,
  }));
  return { labels, datasets };
});

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'top',
    },
    tooltip: {
      mode: 'index',
      intersect: false,
    },
  },
  interaction: {
    mode: 'nearest',
    axis: 'x',
    intersect: false,
  },
  scales: {
    x: {
      title: { display: true, text: 'Time' },
    },
    y: {
      title: { display: true, text: 'Value' },
      beginAtZero: true,
    },
  },
};

const displayRows = computed(() => {
  if (!analysis.value?.data_points?.length) {
    return [];
  }
  return analysis.value.data_points.slice(0, 50);
});

const formattedPeriod = computed(() => {
  if (!analysis.value?.period) return '';
  const { start, end } = analysis.value.period;
  return `${formatTimestamp(start)} → ${formatTimestamp(end)}`;
});

const formatTimestamp = (value) => {
  if (!value) return '—';
  return toIsoLocalString(value).replace('T', ' ');
};

const formatNumber = (value) => {
  if (value == null || Number.isNaN(Number(value))) {
    return '—';
  }
  const numeric = Number(value);
  if (Math.abs(numeric) >= 1000) {
    return numeric.toLocaleString(undefined, { maximumFractionDigits: 1 });
  }
  return numeric.toFixed(2);
};

const describeMetric = (key) => {
  switch (key) {
    case 'mae':
      return 'Mean absolute error across the selected window';
    case 'rmse':
      return 'Root mean square error highlighting spikes';
    case 'r2_score':
      return 'Coefficient of determination vs. actuals';
    case 'mape':
      return 'Mean absolute percentage error';
    default:
      return 'Aggregated metric from the selected period';
  }
};

const buildPayload = () => {
  const start = new Date(`${startDate.value}T00:00:00`);
  const end = new Date(`${endDate.value}T23:59:59`);
  return {
    start_date: start.toISOString(),
    end_date: end.toISOString(),
    aggregation: aggregation.value,
    metrics: ['mae', 'rmse', 'r2_score'],
  };
};

const runAnalysis = async () => {
  loading.value = true;
  error.value = '';
  try {
    analysis.value = await fetchHistoricalAnalysis(buildPayload());
  } catch (err) {
  const detail = err?.response?.data?.detail;
  if (detail === 'No data points within the requested window') {
    error.value = `Không có dữ liệu trong khoảng thời gian đã chọn. Vui lòng chọn thời gian từ ${MIN_DATA_DATE} đến ${MAX_DATA_DATE}.`;
  } else if (detail === 'Not enough data points to analyse the selected window') {
    error.value = 'Khoảng thời gian quá ngắn để phân tích. Hãy chọn ít nhất hai mốc thời gian.';
  } else {
    error.value = detail ?? err?.message ?? 'Analysis request failed';
  }
  } finally {
    loading.value = false;
  }
};

onMounted(runAnalysis);
</script>

<style scoped src="../styles/components/HistoricalAnalysis.css"></style>
