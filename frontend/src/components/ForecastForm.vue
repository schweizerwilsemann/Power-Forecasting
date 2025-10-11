<template>
  <section>
    <h2>Generate Forecast</h2>
    <div class="form-row">
      <label>Mode</label>
      <select v-model="mode">
        <option value="next">Next 15-minute step</option>
        <option value="batch">Batch forecast (future weather)</option>
      </select>
    </div>

    <form @submit.prevent="handleSubmit">
      <div v-if="mode === 'next'" class="form-row two-column">
        <div>
          <label for="horizon">Horizon (steps)</label>
            <input id="horizon" type="number" min="1" v-model.number="singleParams.horizon" />
        </div>
        <div>
          <label class="checkbox">
            <input type="checkbox" v-model="singleParams.includeComponents" />
            Include tree leaf indices
          </label>
        </div>
      </div>

      <div v-else>
        <p>Paste future weather rows (CSV header + rows) matching Renewable.csv columns.</p>
        <textarea rows="8" v-model="batchParams.futureCsv" placeholder="Time,Energy delta[Wh],GHI,..."></textarea>
        <label for="timestamps">Optional timestamps override (comma separated)</label>
          <input id="timestamps" type="text" v-model="batchParams.timestamps" placeholder="2022-09-01T12:00Z,2022-09-01T12:15Z" />
      </div>

      <div style="margin-top: 1rem;">
        <button type="submit" :disabled="loading">
          {{ loading ? 'Running...' : 'Forecast' }}
        </button>
      </div>
    </form>
  </section>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue';

const props = defineProps({
  loading: { type: Boolean, default: false },
});

const emit = defineEmits(['forecast']);
const mode = ref('next');

const singleParams = reactive({
  horizon: 1,
  includeComponents: false,
});

const batchParams = reactive({
  futureCsv: '',
  timestamps: '',
});

watch(
  () => mode.value,
  () => {
    batchParams.futureCsv = '';
    batchParams.timestamps = '';
  },
);

const parsedBatchPayload = computed(() => {
  const block = batchParams.futureCsv.trim();
  if (!block) return null;

  const rows = block.split(/\r?\n/).map((r) => r.trim()).filter(Boolean);
  const header = rows.shift();
  if (!header) return null;

  // Normalize common header variants to the backend-expected names
  const headerMap = {
    time: 'Time',
    timestamp: 'Time',
    date: 'Time',

    'energy delta[wh]': 'Energy delta[Wh]',
    energy: 'Energy delta[Wh]',
    'energy_wh': 'Energy delta[Wh]',

    ghi: 'GHI',
    temp: 'temp',
    temperature: 'temp',
    pressure: 'pressure',
    humidity: 'humidity',
    'wind speed': 'wind_speed',
    wind: 'wind_speed',
    wind_speed: 'wind_speed',
    clouds: 'clouds_all',
    clouds_all: 'clouds_all',
    rain_1h: 'rain_1h',
    snow_1h: 'snow_1h',
    issun: 'isSun',
    'sunlighttime': 'sunlightTime',
    'sunlighttime/daylength': 'SunlightTime/daylength',
    daylength: 'SunlightTime/daylength',
  };

  const headers = header.split(',').map((item) => {
    const key = item.trim();
    const mapped = headerMap[key.toLowerCase()];
    return mapped || key;
  });

  // We require a Time column for the backend to parse timestamps
  if (!headers.includes('Time')) return null;

  const dataRows = rows.filter(Boolean);
  if (!dataRows.length) return null;

  return dataRows.map((row) => {
    const values = row.split(',');
    return values.reduce((acc, value, index) => {
      const key = headers[index];
      if (!key) return acc;
      const trimmed = value.trim();
      if (key === 'Time') {
        // Keep Time as provided; backend parses with dayfirst=True
        acc[key] = trimmed;
        return acc;
      }

      if (trimmed === '') {
        // Use null for missing numeric values so pandas treats them as NaN
        acc[key] = null;
        return acc;
      }

      const num = Number(trimmed);
      acc[key] = Number.isFinite(num) ? num : trimmed;
      return acc;
    }, {});
  });
});

const handleSubmit = () => {
  if (mode.value === 'next') {
    emit('forecast', { mode: 'next', payload: { ...singleParams } });
    return;
  }

  if (!parsedBatchPayload.value) {
    alert('Provide at least one future row.');
    return;
  }

  emit('forecast', {
    mode: 'batch',
    payload: {
      future_weather: parsedBatchPayload.value,
      timestamps: batchParams.timestamps
        ? batchParams.timestamps.split(',').map((item) => item.trim())
        : undefined,
    },
  });
};
</script>

<style scoped>
.checkbox {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
textarea {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
}
</style>

