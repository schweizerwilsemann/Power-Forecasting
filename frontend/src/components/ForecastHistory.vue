<template>
  <section>
    <div class="section-heading">
      <div>
        <p class="eyebrow">Replay</p>
        <h2>Recent Runs</h2>
      </div>
      <p class="muted" v-if="items.length">Tap restore to rehydrate any snapshot.</p>
    </div>

    <div v-if="!items.length" class="empty">
      Completed forecasts will show up here with quick stats you can revisit.
    </div>

    <ul v-else class="history-list">
      <li v-for="entry in items" :key="entry.id">
        <header class="history-header">
          <div>
            <p class="eyebrow mode-label">{{ entry.modeLabel }}</p>
            <strong>{{ entry.steps }} steps · {{ formatWh(entry.stats.total) }}</strong>
            <p class="timestamp">{{ entry.createdLabel }}</p>
          </div>
          <button class="ghost-button" type="button" @click="$emit('restore', entry.id)">
            Restore view
          </button>
        </header>

        <p class="range" v-if="entry.range">
          {{ entry.range.start }} — {{ entry.range.end }}
        </p>

        <dl class="stat-grid">
          <div>
            <dt>Peak</dt>
            <dd>{{ formatWh(entry.stats.max) }}</dd>
          </div>
          <div>
            <dt>Average</dt>
            <dd>{{ formatWh(entry.stats.avg) }}</dd>
          </div>
          <div>
            <dt>Minimum</dt>
            <dd>{{ formatWh(entry.stats.min) }}</dd>
          </div>
        </dl>
      </li>
    </ul>
  </section>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  history: {
    type: Array,
    default: () => [],
  },
});

defineEmits(['restore']);

const numberFormatter = new Intl.NumberFormat('en', {
  maximumFractionDigits: 1,
});

const dateFormatter = new Intl.DateTimeFormat(undefined, {
  day: 'numeric',
  month: 'short',
  hour: '2-digit',
  minute: '2-digit',
});

const formatWh = (value) => {
  if (!Number.isFinite(value)) return '–';
  return `${numberFormatter.format(value)} Wh`;
};

const formatTimestamp = (value) => {
  if (!value) return '';
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return dateFormatter.format(parsed);
};

const items = computed(() =>
  props.history.map((entry) => ({
    ...entry,
    createdLabel: formatTimestamp(entry.createdAt),
  })),
);
</script>

<style scoped src="../styles/components/ForecastHistory.css"></style>
