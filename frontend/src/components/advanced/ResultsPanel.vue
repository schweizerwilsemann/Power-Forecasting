<template>
  <div class="results-panel">
    <div class="panel-section">
      <h3>Forecast Results</h3>

      <div v-if="!results.length" class="empty-state">
        <div class="empty-icon">📊</div>
        <p>No forecast data available. Generate a forecast to see results.</p>
      </div>

      <div v-else class="results-content">
        <div class="summary-stats">
          <div class="stat-item">
            <span class="stat-label">Average Prediction</span>
            <span class="stat-value">{{ averagePrediction }} Wh</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">Confidence Range</span>
            <span class="stat-value">{{ confidenceRange }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">Model Used</span>
            <span class="stat-value">{{ modelUsed }}</span>
          </div>
        </div>

        <div class="chart-container">
          <Line :data="chartData" :options="chartOptions" />
        </div>

        <div class="detailed-results">
          <div class="detailed-results__header">
            <h4>Detailed Results</h4>
            <p>Per-step view with deltas and confidence bands</p>
          </div>
          <div class="result-cards">
            <article
              v-for="result in decoratedResults"
              :key="result.id"
              class="result-card"
              :class="`result-card--${result.intent}`"
            >
              <div class="result-card__head">
                <div>
                  <p class="result-card__time">{{ result.label }}</p>
                  <p class="result-card__scenario">{{ result.scenarioLabel }}</p>
                </div>
                <span class="result-card__step">Step {{ result.stepLabel }}</span>
              </div>
              <div class="result-card__prediction">
                <div>
                  <strong>{{ formatWh(result.prediction_wh) }}</strong>
                  <span class="result-card__units">Predicted</span>
                </div>
                <span class="result-card__delta" :class="`result-card__delta--${result.intent}`">
                  {{ result.deltaLabel }}
                </span>
              </div>
              <div class="result-card__progress">
                <span class="result-card__bar" :style="{ width: result.fill + '%' }"></span>
              </div>
              <div class="result-card__confidence" :class="{ 'result-card__confidence--missing': !result.confidence_interval }">
                <span class="confidence-chip" :class="{ 'confidence-chip--muted': !result.confidence_interval }">
                  Confidence
                </span>
                <span>{{ result.confidence_interval ? result.confidenceText : 'No confidence band' }}</span>
              </div>
            </article>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
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

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

const props = defineProps({
  results: {
    type: Array,
    required: true,
  },
  modelUsed: {
    type: String,
    default: '',
  },
});

const formatWh = (value) => `${Number(value ?? 0).toFixed(1)} Wh`;

const formatConfidence = (interval) => {
  if (!interval) return 'No confidence band';
  return `${formatWh(interval.lower)} - ${formatWh(interval.upper)}`;
};

const chartData = computed(() => {
  if (!props.results.length) return { labels: [], datasets: [] };

  const labels = props.results.map((result, index) => result.timestamp || `Step ${index + 1}`);
  const predictions = props.results.map((result) => result.prediction_wh);
  const upperBounds = props.results.map(
    (result) => result.confidence_interval?.upper ?? result.prediction_wh,
  );
  const lowerBounds = props.results.map(
    (result) => result.confidence_interval?.lower ?? result.prediction_wh,
  );

  return {
    labels,
    datasets: [
      {
        label: 'Prediction',
        data: predictions,
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        fill: false,
        tension: 0.4,
        pointRadius: 4,
        pointHoverRadius: 6,
      },
      {
        label: 'Confidence Upper',
        data: upperBounds,
        borderColor: '#10b981',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        fill: '+1',
        tension: 0.4,
        pointRadius: 2,
        pointHoverRadius: 4,
      },
      {
        label: 'Confidence Lower',
        data: lowerBounds,
        borderColor: '#10b981',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        fill: false,
        tension: 0.4,
        pointRadius: 2,
        pointHoverRadius: 4,
      },
    ],
  };
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
      callbacks: {
        label: (context) => {
          const label = context.dataset.label || '';
          const value = context.parsed.y;
          return `${label}: ${value.toFixed(1)} Wh`;
        },
      },
    },
  },
  scales: {
    x: {
      display: true,
      title: {
        display: true,
        text: 'Time Steps',
      },
    },
    y: {
      display: true,
      title: {
        display: true,
        text: 'Power (Wh)',
      },
      beginAtZero: true,
    },
  },
  interaction: {
    mode: 'nearest',
    axis: 'x',
    intersect: false,
  },
};

const averagePrediction = computed(() => {
  if (!props.results.length) return 0;
  const sum = props.results.reduce((acc, result) => acc + result.prediction_wh, 0);
  return (sum / props.results.length).toFixed(1);
});

const confidenceRange = computed(() => {
  if (!props.results.length || !props.results[0].confidence_interval) return 'N/A';
  return formatConfidence(props.results[0].confidence_interval);
});

const decoratedResults = computed(() => {
  if (!props.results.length) return [];
  const maxPrediction = Math.max(
    ...props.results.map((result) => Number(result.prediction_wh) || 0),
    0,
  );

  return props.results.map((result, index) => {
    const label = result.timestamp || `Step ${index + 1}`;
    const scenarioLabel = result.scenario_name || `Scenario ${index + 1}`;
    const previous = props.results[index - 1]?.prediction_wh;
    const delta = Number.isFinite(previous) ? result.prediction_wh - previous : null;
    const deltaLabel = delta == null ? 'Baseline' : `${delta > 0 ? '+' : ''}${delta.toFixed(1)} Wh`;
    const intent = delta == null ? 'flat' : delta > 1 ? 'up' : delta < -1 ? 'down' : 'flat';
    const fill = maxPrediction ? Math.max(6, (result.prediction_wh / maxPrediction) * 100) : 0;

    return {
      ...result,
      id: `${label}-${index}`,
      label,
      scenarioLabel,
      stepLabel: String(index + 1).padStart(2, '0'),
      deltaLabel,
      intent,
      fill: Number(fill.toFixed(2)),
      confidenceText: formatConfidence(result.confidence_interval),
    };
  });
});
</script>
