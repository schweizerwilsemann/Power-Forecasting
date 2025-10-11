<template>
  <section>
    <h2>Forecast Output</h2>
    <div v-if="!series.length" class="empty">No data yet. Run a forecast to see results.</div>
    <Line v-else :data="chartData" :options="options" />
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
});

const chartData = computed(() => ({
  labels: props.series.map((item, index) => item.timestamp ?? `Step ${index}`),
  datasets: [
    {
      label: 'Predicted (Wh)',
      data: props.series.map((item) => item.prediction_wh),
      borderColor: '#2563eb',
      backgroundColor: 'rgba(37, 99, 235, 0.2)',
    },
  ],
}));

const options = {
  responsive: true,
  scales: {
    y: {
      beginAtZero: true,
    },
  },
};
</script>

<style scoped>
.empty {
  padding: 1.5rem;
  text-align: center;
  color: #64748b;
  background: #f1f5f9;
  border-radius: 12px;
}
</style>
