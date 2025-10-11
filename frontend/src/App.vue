<template>
  <main class="page">
    <header>
      <div>
        <h1>PV Power Forecasting</h1>
        <p>LightGBM-based renewable energy prediction with FastAPI backend.</p>
      </div>
    </header>

    <section v-if="metrics" class="card-grid">
      <div class="metric">
        <span>Forecast horizon</span>
        <strong>{{ metrics.horizon }} × 15 min</strong>
      </div>
      <div class="metric">
        <span>MAE</span>
        <strong>{{ metrics.mae.toFixed(2) }} Wh</strong>
      </div>
      <div class="metric">
        <span>RMSE</span>
        <strong>{{ metrics.rmse.toFixed(2) }} Wh</strong>
      </div>
    </section>

    <ForecastForm :loading="loading" @forecast="triggerForecast" />
    <ForecastChart :series="results" />
  </main>
</template>

<script setup>
import { onMounted, ref } from 'vue';
import ForecastChart from './components/ForecastChart.vue';
import ForecastForm from './components/ForecastForm.vue';
import { useForecastApi } from './composables/useForecastApi';

const results = ref([]);
const loading = ref(false);
const metrics = ref(null);
const { fetchNext, fetchBatch, fetchMetrics } = useForecastApi();

const triggerForecast = async ({ mode, payload }) => {
  loading.value = true;
  try {
    const response = mode === 'next' ? await fetchNext(payload) : await fetchBatch(payload);
    results.value = Array.isArray(response) ? response : [response];
  } catch (error) {
    alert(error?.response?.data?.detail ?? error.message ?? 'Request failed');
  } finally {
    loading.value = false;
  }
};

onMounted(async () => {
  try {
    metrics.value = await fetchMetrics();
  } catch (error) {
    console.warn('Unable to load metrics', error);
  }
});
</script>
