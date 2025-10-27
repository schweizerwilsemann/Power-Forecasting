<template>
  <div class="advanced-forecast">
    <div class="section-header">
      <h2>Advanced Forecasting</h2>
      <p>Generate forecasts with confidence intervals, ensemble models, and multiple scenarios</p>
    </div>

    <div class="forecast-grid">
      <div class="config-panel">
        <ForecastConfigPanel
          :horizon="config.horizon"
          :horizon-options="horizonOptions"
          :include-confidence="config.includeConfidence"
          :ensemble-mode="config.ensembleMode"
          :scenario-count="config.scenarioCount"
          :loading="loading"
          @update:horizon="config.horizon = $event"
          @update:includeConfidence="config.includeConfidence = $event"
          @update:ensembleMode="config.ensembleMode = $event"
          @update:scenarioCount="config.scenarioCount = $event"
          @generate="generateForecast"
        />

        <ScenarioList
          v-if="config.scenarioCount > 1"
          :scenarios="weatherScenarios"
          :limit="config.scenarioCount"
          @update-scenario="updateScenarioValue"
        />
      </div>

      <ResultsPanel
        :results="results"
        :model-used="modelUsed"
      />
    </div>

    <ExportActions
      v-if="results.length"
      @export:csv="exportCSV"
      @export:json="exportJSON"
      @export:clipboard="copyToClipboard"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue';
import ForecastConfigPanel from './advanced/ForecastConfigPanel.vue';
import ScenarioList from './advanced/ScenarioList.vue';
import ResultsPanel from './advanced/ResultsPanel.vue';
import ExportActions from './advanced/ExportActions.vue';

const props = defineProps({
  availableHorizons: {
    type: Array,
    default: () => [],
  },
});

const loading = ref(false);
const results = ref([]);
const modelUsed = ref('');

const config = reactive({
  horizon: 4,
  includeConfidence: true,
  ensembleMode: false,
  scenarioCount: 1,
});

const scenarioTemplates = [
  { name: 'Optimistic', ghi: 800, temp: 25, clouds: 20, windSpeed: 3 },
  { name: 'Realistic', ghi: 600, temp: 22, clouds: 40, windSpeed: 4 },
  { name: 'Pessimistic', ghi: 300, temp: 18, clouds: 80, windSpeed: 6 },
  { name: 'Stormy', ghi: 150, temp: 16, clouds: 90, windSpeed: 8 },
  { name: 'Clear Skies', ghi: 950, temp: 28, clouds: 10, windSpeed: 2 },
];

const weatherScenarios = ref(scenarioTemplates.map((template) => ({ ...template })));

const activeScenarios = computed(() => weatherScenarios.value.slice(0, config.scenarioCount));
const horizonOptions = computed(() => {
  const base = Array.isArray(props.availableHorizons) ? props.availableHorizons : [];
  const filtered = base.filter((value) => Number.isInteger(value) && value > 0);
  if (filtered.length) {
    return [...new Set(filtered)].sort((a, b) => a - b);
  }
  return [1];
});

watch(
  horizonOptions,
  (options) => {
    if (!options.includes(config.horizon)) {
      config.horizon = options[0];
    }
  },
  { immediate: true },
);

const latestRequestId = ref(0);

const cloneResult = (item) => ({
  ...item,
  confidence_interval: item.confidence_interval ? { ...item.confidence_interval } : undefined,
});

const buildSingleSeries = (baseResult, horizon) => {
  const anchor = baseResult.timestamp ? new Date(baseResult.timestamp) : new Date();
  return Array.from({ length: horizon }, (_, idx) => {
    const timestamp = new Date(anchor.getTime() + idx * 15 * 60000).toISOString();
    return cloneResult({
      ...baseResult,
      timestamp,
      step_index: idx + 1,
    });
  });
};

const sortScenarioResults = (results) => {
  return results
    .slice()
    .sort((a, b) => {
      const scenarioCompare = (a.scenario_name || '').localeCompare(b.scenario_name || '');
      if (scenarioCompare !== 0) return scenarioCompare;
      const stepA = a.step_index ?? 0;
      const stepB = b.step_index ?? 0;
      if (stepA !== stepB) return stepA - stepB;
      const timeA = a.timestamp || '';
      const timeB = b.timestamp || '';
      if (timeA && timeB) return timeA.localeCompare(timeB);
      return 0;
    });
};

const updateScenarioValue = ({ index, key, value }) => {
  if (!weatherScenarios.value[index]) {
    return;
  }
  weatherScenarios.value[index] = {
    ...weatherScenarios.value[index],
    [key]: value,
  };
};

const generateForecast = async () => {
  const requestId = Date.now();
  latestRequestId.value = requestId;
  loading.value = true;
  try {
    const scenarioCount = Number(config.scenarioCount) || 1;
    if (scenarioCount === 1) {
      const response = await fetch('/forecast/advanced', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          horizon: config.horizon,
          include_confidence: config.includeConfidence,
          ensemble_mode: config.ensembleMode,
        }),
      });

      if (!response.ok) {
        throw new Error('Advanced forecast request failed');
      }

      const data = await response.json();
      if (latestRequestId.value !== requestId) return;
      results.value = buildSingleSeries(data, config.horizon);
      modelUsed.value = data.model_used || 'lightgbm';
    } else {
      const scenarios = activeScenarios.value.map((scenario) => ({
        name: scenario.name,
        GHI: scenario.ghi,
        temp: scenario.temp,
        clouds_all: scenario.clouds,
        wind_speed: scenario.windSpeed,
      }));

      const response = await fetch('/forecast/scenarios', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          weather_scenarios: scenarios,
          horizon: config.horizon,
          include_confidence: config.includeConfidence,
          ensemble_mode: config.ensembleMode,
        }),
      });

      if (!response.ok) {
        throw new Error('Scenario forecast request failed');
      }

      const data = await response.json();
      if (latestRequestId.value !== requestId) return;
      results.value = sortScenarioResults(data.map(cloneResult));
      modelUsed.value = 'ensemble';
    }
  } catch (error) {
    console.error('Forecast generation failed:', error);
    alert('Failed to generate forecast. Please try again.');
  } finally {
    if (latestRequestId.value === requestId) {
      loading.value = false;
    }
  }
};

const exportCSV = () => {
  if (!results.value.length) return;

  const headers = ['timestamp', 'prediction_wh', 'confidence_lower', 'confidence_upper', 'scenario_name'];
  const rows = results.value.map((result) => [
    result.timestamp || '',
    result.prediction_wh,
    result.confidence_interval?.lower || '',
    result.confidence_interval?.upper || '',
    result.scenario_name || '',
  ]);

  const csv = [headers, ...rows]
    .map((row) => row.map((cell) => `"${cell}"`).join(','))
    .join('\n');

  downloadFile(csv, 'advanced-forecast.csv', 'text/csv');
};

const exportJSON = () => {
  if (!results.value.length) return;

  const json = JSON.stringify(
    {
      config,
      results: results.value,
      generated_at: new Date().toISOString(),
    },
    null,
    2,
  );

  downloadFile(json, 'advanced-forecast.json', 'application/json');
};

const copyToClipboard = async () => {
  if (!results.value.length) return;

  const text = results.value
    .map((result, index) => {
      const base = `Step ${index + 1}: ${result.prediction_wh.toFixed(1)} Wh`;
      if (!result.confidence_interval) {
        return base;
      }
      const { lower, upper } = result.confidence_interval;
      return `${base} (${lower.toFixed(1)}-${upper.toFixed(1)})`;
    })
    .join('\n');

  try {
    await navigator.clipboard.writeText(text);
    alert('Results copied to clipboard!');
  } catch (error) {
    console.error('Failed to copy to clipboard:', error);
  }
};

const downloadFile = (content, filename, mimeType) => {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

watch(
  () => config.scenarioCount,
  (newCount) => {
    const count = Number(newCount) || 1;
    while (weatherScenarios.value.length < count) {
      const template =
        scenarioTemplates[weatherScenarios.value.length] ?? {
          name: `Scenario ${weatherScenarios.value.length + 1}`,
          ghi: 500,
          temp: 22,
          clouds: 50,
          windSpeed: 4,
        };
      weatherScenarios.value.push({ ...template });
    }
    if (!loading.value) {
      results.value = [];
    }
  },
);

watch(
  () => [config.horizon, config.includeConfidence, config.ensembleMode],
  () => {
    if (!loading.value) {
      results.value = [];
    }
  },
);

watch(
  weatherScenarios,
  () => {
    if (!loading.value) {
      results.value = [];
    }
  },
  { deep: true },
);
</script>

<style scoped src="../styles/components/AdvancedForecast.css"></style>
