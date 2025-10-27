<template>
  <div class="panel-section">
    <h3>Forecast Configuration</h3>

    <div class="form-group">
      <label for="horizon">Forecast Horizon</label>
      <select id="horizon" v-model.number="horizonModel">
        <option :value="1">1 Step (15 minutes)</option>
        <option :value="4">4 Steps (1 hour)</option>
        <option :value="8">8 Steps (2 hours)</option>
        <option :value="24">24 Steps (6 hours)</option>
        <option :value="48">48 Steps (12 hours)</option>
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
</script>
