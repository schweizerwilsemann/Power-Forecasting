<template>
  <section>
    <div class="section-heading">
      <h2>Forecast Output</h2>
      <button
        v-if="downloadable && series.length"
        type="button"
        class="ghost-button"
        @click="$emit('download')"
      >
        Download CSV
      </button>
    </div>
    <div v-if="!series.length" class="empty">No data yet. Run a forecast to see results.</div>
    <div v-else class="chart-shell">
      <Line :data="chartData" :options="options" />
    </div>
  </section>
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
  series: {
    type: Array,
    default: () => [],
  },
  downloadable: {
    type: Boolean,
    default: false,
  },
});

defineEmits(['download']);

const chartData = computed(() => ({
  labels: props.series.map((item, index) => item.timestamp ?? `Step ${index}`),
  datasets: [
    {
      label: 'Predicted (Wh)',
      data: props.series.map((item) => item.prediction_wh),
      borderColor: '#3b82f6',
      backgroundColor: 'rgba(59, 130, 246, 0.18)',
      fill: {
        target: 'origin',
        above: 'rgba(59, 130, 246, 0.18)',
        below: 'rgba(59, 130, 246, 0.08)',
      },
      tension: 0.35,
      borderWidth: 3,
      pointRadius: 3.5,
      pointHoverRadius: 6,
    },
  ],
}));

const options = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false,
    },
    tooltip: {
      backgroundColor: '#0f172a',
      borderWidth: 0,
      padding: 12,
      titleFont: { size: 14 },
      bodyFont: { size: 13 },
      displayColors: false,
      callbacks: {
        label: (context) => `${context.formattedValue} Wh`,
      },
    },
  },
  scales: {
    y: {
      beginAtZero: true,
      grid: {
        color: 'rgba(148, 163, 184, 0.25)',
      },
      ticks: {
        color: 'rgba(15, 23, 42, 0.7)',
      },
    },
    x: {
      grid: {
        display: false,
      },
      ticks: {
        color: 'rgba(15, 23, 42, 0.7)',
      },
    },
  },
};
</script>

<style scoped src="../styles/components/ForecastChart.css"></style>
