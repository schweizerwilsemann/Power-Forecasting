<template>
  <section>
    <div class="section-heading">
      <div>
        <p class="eyebrow">Model outlook</p>
        <h2>Forecast Insights</h2>
      </div>
      <p v-if="stats" class="muted">Auto-generated from the current forecast window.</p>
    </div>

    <div v-if="!stats" class="empty">Run a forecast to unlock contextual insights.</div>

    <div v-else>
      <div class="insights-grid">
        <article v-for="card in insightCards" :key="card.label" class="insight-card">
          <small>{{ card.label }}</small>
          <strong>{{ card.value }}</strong>
          <p>{{ card.detail }}</p>
        </article>
      </div>

      <ul v-if="metaInsights.length" class="insight-list">
        <li v-for="(item, index) in metaInsights" :key="index">
          <span class="pulse" :class="item.intent" aria-hidden="true"></span>
          <div>
            <strong>{{ item.title }}</strong>
            <p>{{ item.description }}</p>
          </div>
        </li>
      </ul>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  series: {
    type: Array,
    default: () => [],
  },
  metrics: {
    type: Object,
    default: null,
  },
});

const numberFormatter = new Intl.NumberFormat('en', {
  maximumFractionDigits: 1,
});

const percentFormatter = new Intl.NumberFormat('en', {
  style: 'percent',
  maximumFractionDigits: 0,
});

const finiteSeries = computed(() =>
  props.series
    .map((point) => Number(point?.prediction_wh))
    .filter((value) => Number.isFinite(value)),
);

const stats = computed(() => {
  if (!finiteSeries.value.length) return null;

  const values = finiteSeries.value;
  const max = Math.max(...values);
  const min = Math.min(...values);
  const avg = values.reduce((sum, value) => sum + value, 0) / values.length;
  const first = values[0];
  const last = values[values.length - 1];
  const trend = last - first;
  const deltas = values.slice(1).map((value, index) => value - values[index]);
  const volatility = deltas.length
    ? Math.sqrt(deltas.reduce((sum, value) => sum + value * value, 0) / deltas.length)
    : 0;

  return { max, min, avg, first, last, trend, volatility };
});

const confidenceScore = computed(() => {
  if (!props.metrics) return null;
  const base = Number.isFinite(props.metrics.rmse)
    ? props.metrics.rmse
    : Number.isFinite(props.metrics.mae)
    ? props.metrics.mae
    : null;

  if (!Number.isFinite(base)) return null;

  // Map RMSE / MAE into a 0-1 band where lower error -> higher confidence.
  const normalized = Math.max(10, Math.min(96, 100 - base / 50));
  return normalized / 100;
});

const formatWh = (value) => `${numberFormatter.format(value)} Wh`;

const insightCards = computed(() => {
  if (!stats.value) return [];

  return [
    {
      label: 'Peak output',
      value: formatWh(stats.value.max),
      detail: 'Highest predicted value within this horizon.',
    },
    {
      label: 'Lowest output',
      value: formatWh(stats.value.min),
      detail: 'Minimum energy pocket to watch for ramp-downs.',
    },
    {
      label: 'Average flow',
      value: formatWh(stats.value.avg),
      detail: 'Mean power balancing out the ups and downs.',
    },
  ];
});

const metaInsights = computed(() => {
  if (!stats.value) return [];

  const items = [];
  const trend = stats.value.trend;

  if (Math.abs(trend) < 1) {
    items.push({
      title: 'Stable output',
      description: 'Predictions stay tightly grouped — expect a steady profile.',
      intent: 'neutral',
    });
  } else if (trend > 0) {
    items.push({
      title: 'Upward momentum',
      description: 'Later timestamps trend higher, suggesting more production ahead.',
      intent: 'positive',
    });
  } else {
    items.push({
      title: 'Cooling pattern',
      description: 'Values ease lower toward the end of the window.',
      intent: 'warning',
    });
  }

  if (stats.value.volatility > 30) {
    items.push({
      title: 'High volatility',
      description: 'Adjacent steps swing sharply — consider shorter dispatch updates.',
      intent: 'warning',
    });
  } else {
    items.push({
      title: 'Calm oscillation',
      description: 'Variance stays low, ideal for smooth grid integration.',
      intent: 'positive',
    });
  }

  if (props.metrics?.horizon) {
    items.push({
      title: `Horizon: ${props.metrics.horizon * 15} minutes`,
      description: 'Each step represents a 15-minute slice of future production.',
      intent: 'neutral',
    });
  }

  if (confidenceScore.value) {
    items.push({
      title: `${percentFormatter.format(confidenceScore.value)} confidence band`,
      description: 'Derived from current MAE / RMSE performance.',
      intent: confidenceScore.value > 0.6 ? 'positive' : 'warning',
    });
  }

  return items;
});
</script>

<style scoped src="../styles/components/ForecastInsights.css"></style>
