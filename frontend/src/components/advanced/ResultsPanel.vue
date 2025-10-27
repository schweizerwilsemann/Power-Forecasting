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
            <p v-if="decoratedScenarioResults.length > 1">Grouped by scenario · each block shows every step</p>
            <p v-else>Per-step view with deltas and confidence bands</p>
          </div>
          <div class="scenario-block" v-for="group in decoratedScenarioResults" :key="group.name">
            <h5 class="scenario-title">{{ group.name }}</h5>
            <div class="result-cards">
              <article
                v-for="result in group.cards"
                :key="result.id"
                class="result-card"
                :class="`result-card--${result.intent}`"
              >
                <div class="result-card__head">
                  <div>
                    <p class="result-card__time">{{ result.label }}</p>
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
                <div
                  class="result-card__confidence"
                  :class="{ 'result-card__confidence--missing': !result.confidence_interval }"
                >
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

const palette = ['#3b82f6', '#0ea5e9', '#10b981', '#f97316', '#a855f7'];

const formatWh = (value) => `${Number(value ?? 0).toFixed(1)} Wh`;

const formatConfidence = (interval) => {
  if (!interval) return 'No confidence band';
  return `${formatWh(interval.lower)} - ${formatWh(interval.upper)}`;
};

const normalizedResults = computed(() => {
  return props.results
    .slice()
    .sort((a, b) => {
      const scenarioCompare = (a.scenario_name || '').localeCompare(b.scenario_name || '');
      if (scenarioCompare !== 0) return scenarioCompare;
      const stepA = a.step_index ?? 0;
      const stepB = b.step_index ?? 0;
      if (stepA !== stepB) return stepA - stepB;
      const timeA = a.timestamp || '';
      const timeB = b.timestamp || '';
      return timeA.localeCompare(timeB);
    });
});

const scenarioGroups = computed(() => {
  if (!normalizedResults.value.length) return [];
  const groups = new Map();
  normalizedResults.value.forEach((result) => {
    const key = result.scenario_name || 'Forecast';
    if (!groups.has(key)) {
      groups.set(key, []);
    }
    groups.get(key).push(result);
  });
  return Array.from(groups.entries()).map(([name, series]) => ({
    name,
    series,
  }));
});

const chartData = computed(() => {
  if (!scenarioGroups.value.length) return { labels: [], datasets: [] };

  if (scenarioGroups.value.length === 1) {
    const series = scenarioGroups.value[0].series;
    const labels = series.map((item, index) => item.timestamp || `Step ${item.step_index ?? index + 1}`);
    const predictions = series.map((item) => item.prediction_wh);
    const upperBounds = series.map(
      (item) => item.confidence_interval?.upper ?? item.prediction_wh,
    );
    const lowerBounds = series.map(
      (item) => item.confidence_interval?.lower ?? item.prediction_wh,
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
  }

  const labels = scenarioGroups.value[0].series.map(
    (item, index) => item.timestamp || `Step ${item.step_index ?? index + 1}`,
  );
  const datasets = scenarioGroups.value.map((group, index) => ({
    label: group.name,
    data: group.series.map((item) => item.prediction_wh),
    borderColor: palette[index % palette.length],
    backgroundColor: `${palette[index % palette.length]}33`,
    fill: false,
    tension: 0.3,
    pointRadius: 3,
    pointHoverRadius: 5,
  }));

  return { labels, datasets };
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
  if (!normalizedResults.value.length) return 0;
  const sum = normalizedResults.value.reduce((acc, result) => acc + result.prediction_wh, 0);
  return (sum / normalizedResults.value.length).toFixed(1);
});

const confidenceRange = computed(() => {
  const intervals = normalizedResults.value
    .map((item) => item.confidence_interval)
    .filter(Boolean);
  if (!intervals.length) return 'N/A';
  const lower = Math.min(...intervals.map((item) => item.lower));
  const upper = Math.max(...intervals.map((item) => item.upper));
  return formatConfidence({ lower, upper });
});

const decoratedScenarioResults = computed(() => {
  return scenarioGroups.value.map((group) => {
    const maxPrediction = Math.max(...group.series.map((item) => Number(item.prediction_wh) || 0), 0) || 1;
    const cards = group.series.map((result, index) => {
      const label = result.timestamp || `Step ${result.step_index ?? index + 1}`;
      const previous = group.series[index - 1]?.prediction_wh;
      const delta = Number.isFinite(previous) ? result.prediction_wh - previous : null;
      const deltaLabel = delta == null ? 'Baseline' : `${delta > 0 ? '+' : ''}${delta.toFixed(1)} Wh`;
      const intent = delta == null ? 'flat' : delta > 1 ? 'up' : delta < -1 ? 'down' : 'flat';
      const fill = maxPrediction ? Math.max(6, (result.prediction_wh / maxPrediction) * 100) : 0;
      return {
        ...result,
        id: `${group.name}-${result.step_index ?? index + 1}-${label}`,
        label,
        stepLabel: String(result.step_index ?? index + 1).padStart(2, '0'),
        deltaLabel,
        intent,
        fill: Number(fill.toFixed(2)),
        confidenceText: formatConfidence(result.confidence_interval),
      };
    });
    return { name: group.name, cards };
  });
});
</script>
