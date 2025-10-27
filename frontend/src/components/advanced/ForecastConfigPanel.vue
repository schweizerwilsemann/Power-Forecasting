<template>
  <div class="panel-section">
    <h3>Forecast Configuration</h3>

    <div class="form-group">
      <label for="horizon">Forecast Horizon</label>
      <select id="horizon" v-model.number="horizonModel">
        <option
          v-for="option in normalizedHorizonOptions"
          :key="`config-${option}`"
          :value="option"
        >
          {{ formatOption(option) }}
        </option>
      </select>
    </div>

    <div class="form-group">
      <label class="checkbox">
        <input type="checkbox" v-model="includeConfidenceModel" />
        Include Confidence Intervals
      </label>
    </div>

    <div class="form-group">
      <label class="checkbox">
        <input type="checkbox" v-model="ensembleModeModel" />
        Use Ensemble Models
      </label>
    </div>

    <div class="form-group">
      <label for="scenarioCount">Weather Scenarios</label>
      <select id="scenarioCount" v-model.number="scenarioCountModel">
        <option :value="1">Single Scenario</option>
        <option :value="3">3 Scenarios</option>
        <option :value="5">5 Scenarios</option>
      </select>
    </div>

    <button
      class="btn btn-primary btn-full"
      style="margin-top: 2%;"
      @click="$emit('generate')"
      :disabled="loading"
    >
      <i class="icon-play"></i>
      {{ loading ? 'Generating...' : 'Generate Forecast' }}
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  horizon: { type: Number, required: true },
  horizonOptions: {
    type: Array,
    default: () => [1, 4, 8, 24, 48],
  },
  includeConfidence: { type: Boolean, required: true },
  ensembleMode: { type: Boolean, required: true },
  scenarioCount: { type: Number, required: true },
  loading: { type: Boolean, default: false },
});

const emit = defineEmits([
  'update:horizon',
  'update:includeConfidence',
  'update:ensembleMode',
  'update:scenarioCount',
  'generate',
]);

const horizonModel = computed({
  get: () => props.horizon,
  set: (value) => emit('update:horizon', Number(value)),
});

const includeConfidenceModel = computed({
  get: () => props.includeConfidence,
  set: (value) => emit('update:includeConfidence', value),
});

const ensembleModeModel = computed({
  get: () => props.ensembleMode,
  set: (value) => emit('update:ensembleMode', value),
});

const scenarioCountModel = computed({
  get: () => props.scenarioCount,
  set: (value) => emit('update:scenarioCount', Number(value)),
});

const normalizedHorizonOptions = computed(() => {
  const base = Array.isArray(props.horizonOptions) ? props.horizonOptions : [];
  const filtered = base.filter((value) => Number.isInteger(value) && value > 0);
  if (filtered.length) {
    return [...new Set(filtered)].sort((a, b) => a - b);
  }
  return [1, 4, 8, 24, 48];
});

const formatOption = (value) => {
  const minutes = value * 15;
  if (minutes % 60 === 0) {
    const hours = minutes / 60;
    return `${value} Step${value > 1 ? 's' : ''} (${hours}hr${hours > 1 ? 's' : ''})`;
  }
  return `${value} Step${value > 1 ? 's' : ''} (${minutes}min)`;
};
</script>
