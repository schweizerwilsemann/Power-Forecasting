<template>
  <div class="model-management">
    <div class="section-header">
      <h2>Model Management</h2>
      <p>Monitor deployed models, trigger retraining, and review lifecycle events</p>
      <button class="btn btn-secondary" @click="refresh" :disabled="loading">
        <i class="icon-refresh"></i>
        {{ loading ? 'Refreshing...' : 'Refresh' }}
      </button>
    </div>

    <div v-if="error" class="alert alert-error">
      {{ error }}
    </div>

    <section v-if="status" class="status-overview">
      <div class="card-grid metrics-grid">
        <article class="metric-card metric-card--light">
          <span>Current model</span>
          <strong>{{ status.current_model }}</strong>
          <p>{{ status.training_status === 'ready' ? 'Ready for inference' : status.training_status }}</p>
        </article>
        <article class="metric-card metric-card--light">
          <span>Available variants</span>
          <strong>{{ status.available_models.length }}</strong>
          <p>{{ status.available_models.join(', ') }}</p>
        </article>
        <article class="metric-card metric-card--light">
          <span>Last trained</span>
          <strong>{{ lastTrainedLabel }}</strong>
          <p>UTC timestamp of the latest training job</p>
        </article>
      </div>
    </section>

    <section v-if="metricRows.length" class="metrics-section">
      <div class="section-header">
        <h3>Model metrics</h3>
        <p>Key performance indicators reported by the backend</p>
      </div>
      <div class="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>Metric</th>
              <th>Value</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="metric in metricRows" :key="metric.label">
              <td>{{ metric.label }}</td>
              <td>{{ metric.value }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="actions-section">
      <div class="section-header">
        <h3>Retraining</h3>
        <p>Start a retraining job and monitor its progress</p>
      </div>
      <div class="actions-card">
        <button class="btn btn-primary" @click="startRetrain" :disabled="retraining">
          <i class="icon-target"></i>
          {{ retraining ? 'Starting...' : 'Trigger retrain' }}
        </button>
        <p class="hint">
          Retraining will enqueue a new job using the latest records in storage. Configure your backend persistence to
          retain job history for long-running audits.
        </p>
        <div v-if="retrainMessage" class="retrain-status">
          <strong>{{ retrainMessage.status }}</strong>
          <span>{{ retrainMessage.message }}</span>
          <span v-if="retrainMessage.estimated_completion" class="eta">
            ETA: {{ formatTimestamp(retrainMessage.estimated_completion) }}
          </span>
        </div>
      </div>
    </section>

    <section v-if="activityLog.length" class="activity-section">
      <div class="section-header">
        <h3>Activity log</h3>
        <p>Latest events recorded for model operations</p>
      </div>
      <ul class="activity-list">
        <li v-for="item in activityLog" :key="item.id" class="activity-item">
          <div class="activity-time">{{ item.time }}</div>
          <div class="activity-body">
            <div class="activity-title">{{ item.title }}</div>
            <div class="activity-message">{{ item.message }}</div>
          </div>
        </li>
      </ul>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import { toIsoLocalString } from '../utils/time';
import { useOperationsApi } from '../composables/useOperationsApi';

const { fetchModelStatus, triggerModelRetrain } = useOperationsApi();

const loading = ref(false);
const retraining = ref(false);
const status = ref(null);
const error = ref('');
const retrainMessage = ref(null);
const activityLog = ref([]);

const metricRows = computed(() => {
  if (!status.value?.model_metrics) return [];
  return Object.entries(status.value.model_metrics).map(([label, value]) => ({
    label: label.toUpperCase(),
    value: formatNumber(value),
  }));
});

const lastTrainedLabel = computed(() => {
  if (!status.value?.last_trained) return 'Unknown';
  return formatTimestamp(status.value.last_trained);
});

const formatNumber = (value) => {
  if (value == null || Number.isNaN(Number(value))) {
    return '—';
  }
  return Number(value).toFixed(3);
};

const formatTimestamp = (value) => {
  if (!value) return '—';
  return toIsoLocalString(value).replace('T', ' ');
};

const pushActivity = (title, message) => {
  activityLog.value.unshift({
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
    time: formatTimestamp(new Date().toISOString()),
    title,
    message,
  });
  activityLog.value = activityLog.value.slice(0, 10);
};

const refresh = async () => {
  loading.value = true;
  error.value = '';
  try {
    status.value = await fetchModelStatus();
    pushActivity('Status refreshed', `Current model: ${status.value.current_model}`);
  } catch (err) {
    error.value = err?.response?.data?.detail ?? err?.message ?? 'Unable to load model status';
  } finally {
    loading.value = false;
  }
};

const startRetrain = async () => {
  retraining.value = true;
  try {
    const response = await triggerModelRetrain();
    retrainMessage.value = response;
    pushActivity('Retraining triggered', response.message || 'Retraining job started');
  } catch (err) {
    error.value = err?.response?.data?.detail ?? err?.message ?? 'Retraining request failed';
  } finally {
    retraining.value = false;
  }
};

onMounted(refresh);
</script>

<style scoped src="../styles/components/ModelManagement.css"></style>
