<template>
  <section class="forecast-form">
    <div class="section-heading">
      <div>
        <p class="eyebrow">Inputs</p>
        <h2>Generate Forecast</h2>
      </div>
      <p class="muted">Switch between a single next step or a batch of weather rows.</p>
    </div>

    <form @submit.prevent="handleSubmit">
      <div class="mode-toggle" role="group" aria-label="Forecast mode">
        <button
          type="button"
          :class="['mode-pill', { active: mode === 'next' }]"
          :aria-pressed="mode === 'next'"
          @click="mode = 'next'"
        >
          <strong>Immediate</strong>
          <span>Predict the next horizon</span>
        </button>
        <button
          type="button"
          :class="['mode-pill', { active: mode === 'batch' }]"
          :aria-pressed="mode === 'batch'"
          @click="mode = 'batch'"
        >
          <strong>Batch</strong>
          <span>Upload future weather</span>
        </button>
      </div>

      <div v-if="mode === 'next'" class="form-row two-column">
        <div>
          <label for="horizon">Horizon (steps)</label>
          <select
            v-if="sanitizedHorizonOptions.length"
            id="horizon"
            v-model.number="singleParams.horizon"
          >
            <option
              v-for="option in sanitizedHorizonOptions"
              :key="option"
              :value="option"
            >
              {{ describeHorizon(option) }}
            </option>
          </select>
          <input
            v-else
            id="horizon"
            type="number"
            min="1"
            v-model.number="singleParams.horizon"
          />
          <small class="helper">Each step equals 15 minutes.</small>
        </div>
        <div>
          <label class="checkbox">
            <input type="checkbox" v-model="singleParams.includeComponents" />
            Include tree leaf indices
          </label>
          <small class="helper">Surface raw LightGBM decision paths.</small>
        </div>
      </div>

      <div v-else class="form-stack">
        <p class="helper">
          Paste future weather rows (CSV header + rows) matching <code>Renewable.csv</code>. We will normalize
          common column aliases for you.
        </p>
        <div class="form-row two-column">
          <div>
            <label for="batch-horizon">Horizon (steps)</label>
            <select
              v-if="sanitizedHorizonOptions.length"
              id="batch-horizon"
              v-model.number="batchParams.horizon"
            >
              <option
                v-for="option in sanitizedHorizonOptions"
                :key="`batch-${option}`"
                :value="option"
              >
                {{ describeHorizon(option) }}
              </option>
            </select>
            <input
              v-else
              id="batch-horizon"
              type="number"
              min="1"
              v-model.number="batchParams.horizon"
            />
            <small class="helper">Each step equals 15 minutes.</small>
          </div>
        </div>
        <button class="link-button" type="button" @click="loadSampleData">
          Need a template? Insert sample data
        </button>
        <textarea
          rows="8"
          v-model="batchParams.futureCsv"
          placeholder="Time,Energy delta[Wh],GHI,..."
          spellcheck="false"
        ></textarea>
        <label for="timestamps">Optional timestamps override (comma separated)</label>
        <input
          id="timestamps"
          type="text"
          v-model="batchParams.timestamps"
          placeholder="2022-09-01T12:00Z,2022-09-01T12:15Z"
        />
      </div>

      <footer class="form-footer">
        <div>
          <p class="muted">The backend validates schema and raises precise errors if columns misalign.</p>
        </div>
        <button type="submit" :disabled="loading">
          {{ loading ? 'Running...' : 'Forecast' }}
        </button>
      </footer>
    </form>
  </section>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue';

const props = defineProps({
  loading: { type: Boolean, default: false },
  horizonOptions: {
    type: Array,
    default: () => [],
  },
});

const emit = defineEmits(['forecast']);
const mode = ref('next');

const sanitizedHorizonOptions = computed(() => {
  const base = Array.isArray(props.horizonOptions) ? props.horizonOptions : [];
  const filtered = base.filter((value) => Number.isInteger(value) && value > 0);
  if (filtered.length) {
    return [...new Set(filtered)].sort((a, b) => a - b);
  }
  return [1];
});

const selectDefaultHorizon = () => sanitizedHorizonOptions.value[0];

const singleParams = reactive({
  horizon: selectDefaultHorizon(),
  includeComponents: false,
});

const batchParams = reactive({
  horizon: selectDefaultHorizon(),
  futureCsv: '',
  timestamps: '',
});

const SAMPLE_BATCH = `Time,Energy delta[Wh],GHI,temp,pressure,humidity,wind_speed,clouds_all,rain_1h,snow_1h,isSun,sunlightTime,SunlightTime/daylength
2024-01-10T08:00Z,120,480,18,1013,45,3.1,20,0,0,1,15000,0.62
2024-01-10T08:15Z,125,512,19,1012,44,3.0,18,0,0,1,15200,0.63
2024-01-10T08:30Z,140,545,20,1011,42,2.8,15,0,0,1,15420,0.65`;

const loadSampleData = () => {
  batchParams.futureCsv = SAMPLE_BATCH;
  batchParams.timestamps = '';
};

const describeHorizon = (value) => `${value} steps (${value * 15} min)`;

watch(
  () => mode.value,
  () => {
    batchParams.futureCsv = '';
    batchParams.timestamps = '';
  },
);

watch(
  sanitizedHorizonOptions,
  (options) => {
    if (!options.includes(singleParams.horizon)) {
      singleParams.horizon = options[0];
    }
    if (!options.includes(batchParams.horizon)) {
      batchParams.horizon = options[0];
    }
  },
  { immediate: true },
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
      horizon: batchParams.horizon,
      future_weather: parsedBatchPayload.value,
      timestamps: batchParams.timestamps
        ? batchParams.timestamps.split(',').map((item) => item.trim())
        : undefined,
    },
  });
};
</script>

<style scoped src="../styles/components/ForecastForm.css"></style>
