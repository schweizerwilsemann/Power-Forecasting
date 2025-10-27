<template>
  <div class="export-section">
    <div class="section-header">
      <h3>Export Results</h3>
    </div>
    <div class="export-options">
      <button class="btn btn-secondary" @click="$emit('export:csv')">
        <i class="icon-download"></i>
        Download CSV
      </button>
      <button class="btn btn-secondary" @click="$emit('export:json')">
        <i class="icon-download"></i>
        Download JSON
      </button>
      <button class="btn btn-secondary" @click="$emit('export:clipboard')">
        <i class="icon-copy"></i>
        Copy to Clipboard
      </button>
    </div>
  </div>
</template>

<script setup>
defineEmits(['export:csv', 'export:json', 'export:clipboard']);
</script>
