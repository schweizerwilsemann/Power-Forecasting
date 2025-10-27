<template>
  <section>
    <div class="section-heading">
      <div>
        <p class="eyebrow">Step-by-step</p>
        <h2>Forecast Timeline</h2>
      </div>
      <p v-if="items.length" class="muted">{{ items.length }} data points rendered.</p>
    </div>

    <div v-if="!items.length" class="empty">Timeline will populate after you run a forecast.</div>

    <ol v-else class="timeline">
      <li v-for="item in items" :key="item.id">
        <div class="time">{{ item.label }}</div>
        <div class="value-row">
          <strong>{{ item.valueLabel }}</strong>
          <span class="delta" :class="item.intent">
            {{ item.deltaLabel }}
          </span>
        </div>
        <div class="bar">
          <span class="fill" :style="{ width: item.fillWidth }"></span>
        </div>
      </li>
    </ol>
  </section>
</template>

<script setup>
import { computed } from 'vue';
import { normalizeTimestamp } from '../utils/time';

const props = defineProps({
  series: {
    type: Array,
    default: () => [],
  },
});

const numberFormatter = new Intl.NumberFormat('en', {
  maximumFractionDigits: 1,
});

const percentFormatter = new Intl.NumberFormat('en', {
  style: 'percent',
  maximumFractionDigits: 0,
});

const normalizedSeries = computed(() =>
  props.series.map((point, index) => {
    const label = point.timestamp ? normalizeTimestamp(point.timestamp) : `Step ${index + 1}`;
    return {
      id: `${label ?? index}-${index}`,
      label,
      value: Number(point?.prediction_wh),
    };
  }),
);

const maxValue = computed(() => {
  const values = normalizedSeries.value.map((item) => item.value).filter((value) => Number.isFinite(value));
  if (!values.length) return 0;
  return Math.max(...values);
});

const items = computed(() => {
  if (!normalizedSeries.value.length) return [];

  return normalizedSeries.value.map((entry, index, array) => {
    const previous = array[index - 1]?.value;
    const delta = Number.isFinite(previous) && Number.isFinite(entry.value) ? entry.value - previous : 0;
    const deltaPercent =
      Number.isFinite(previous) && previous !== 0 ? Math.min(1.5, Math.max(-1.5, delta / previous)) : 0;
    const intent = delta > 0 ? 'up' : delta < 0 ? 'down' : 'flat';
    const fill = maxValue.value ? `${Math.max(4, (entry.value / maxValue.value) * 100).toFixed(2)}%` : '4%';

    return {
      ...entry,
      valueLabel: Number.isFinite(entry.value) ? `${numberFormatter.format(entry.value)} Wh` : '–',
      deltaLabel:
        index === 0 || !Number.isFinite(delta)
          ? 'Baseline'
          : `${delta > 0 ? '+' : ''}${numberFormatter.format(delta)} Wh (${percentFormatter.format(deltaPercent)})`,
      intent,
      fillWidth: fill,
    };
  });
});
</script>

<style scoped src="../styles/components/ForecastTimeline.css"></style>
