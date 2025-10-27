<template>
  <div class="panel-section">
    <h3>Weather Scenarios</h3>
    <div class="scenarios-list">
      <div
        v-for="(scenario, index) in limitedScenarios"
        :key="index"
        class="scenario-item"
      >
        <div class="scenario-item__header">
          <h4>{{ scenario.name }}</h4>
          <span class="scenario-chip">Scenario {{ index + 1 }}</span>
        </div>
        <div class="scenario-inputs">
          <div class="input-group">
            <label>GHI (W/m²)</label>
            <input
              type="number"
              :min="0"
              :max="1500"
              :value="scenario.ghi"
              @input="update(index, 'ghi', $event.target.valueAsNumber ?? 0)"
            />
          </div>
          <div class="input-group">
            <label>Temperature (°C)</label>
            <input
              type="number"
              :min="-20"
              :max="50"
              :value="scenario.temp"
              @input="update(index, 'temp', $event.target.valueAsNumber ?? 0)"
            />
          </div>
          <div class="input-group">
            <label>Clouds (%)</label>
            <input
              type="number"
              :min="0"
              :max="100"
              :value="scenario.clouds"
              @input="update(index, 'clouds', $event.target.valueAsNumber ?? 0)"
            />
          </div>
          <div class="input-group">
            <label>Wind Speed (m/s)</label>
            <input
              type="number"
              :min="0"
              :max="30"
              :value="scenario.windSpeed"
              @input="update(index, 'windSpeed', $event.target.valueAsNumber ?? 0)"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  scenarios: {
    type: Array,
    required: true,
  },
  limit: {
    type: Number,
    default: 1,
  },
});

const emit = defineEmits(['update-scenario']);

const limitedScenarios = computed(() => props.scenarios.slice(0, props.limit));

const update = (index, key, value) => {
  emit('update-scenario', { index, key, value });
};
</script>
