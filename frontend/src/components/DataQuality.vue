<template>
  <div class="data-quality">
    <div class="section-header">
      <h2>Data Quality Management</h2>
      <p>Monitor data quality, detect anomalies, and validate imported data</p>
    </div>

    <!-- Quality Overview -->
    <div class="quality-overview">
      <div class="overview-card">
        <div class="card-header">
          <h3>Overall Quality Score</h3>
          <div class="quality-score" :class="qualityScoreClass">
            {{ dataQuality.quality_score }}%
          </div>
        </div>
        <div class="quality-metrics">
          <div class="metric">
            <span class="metric-label">Completeness</span>
            <div class="metric-bar">
              <div class="metric-fill" :style="{ width: dataQuality.data_completeness + '%' }"></div>
            </div>
            <span class="metric-value">{{ dataQuality.data_completeness }}%</span>
          </div>
          <div class="metric">
            <span class="metric-label">Anomalies</span>
            <div class="metric-bar">
              <div class="metric-fill anomaly" :style="{ width: Math.min(anomalyPercentage, 100) + '%' }"></div>
            </div>
            <span class="metric-value">{{ dataQuality.anomaly_count }}</span>
          </div>
        </div>
      </div>

      <div class="overview-card">
        <div class="card-header">
          <h3>Data Statistics</h3>
        </div>
        <div class="stats-grid">
          <div class="stat">
            <span class="stat-label">Total Records</span>
            <span class="stat-value">{{ dataQuality.total_records.toLocaleString() }}</span>
          </div>
          <div class="stat">
            <span class="stat-label">Last Updated</span>
            <span class="stat-value">{{ formatDate(dataQuality.last_updated) }}</span>
          </div>
          <div class="stat">
            <span class="stat-label">Missing Values</span>
            <span class="stat-value">{{ totalMissingValues }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Missing Values Analysis -->
    <div class="analysis-section">
      <div class="section-header">
        <h3>Missing Values Analysis</h3>
        <button class="btn btn-secondary" @click="refreshData">
          <i class="icon-refresh"></i>
          Refresh
        </button>
      </div>
      
      <div class="missing-values-table">
        <div class="table-header">
          <div>Column</div>
          <div>Missing Count</div>
          <div>Missing %</div>
          <div>Status</div>
        </div>
        <div 
          v-for="(count, column) in dataQuality.missing_values" 
          :key="column"
          class="table-row"
        >
          <div class="column-name">{{ column }}</div>
          <div>{{ count.toLocaleString() }}</div>
          <div>{{ ((count / dataQuality.total_records) * 100).toFixed(2) }}%</div>
          <div class="status" :class="getMissingStatus(count)">
            {{ getMissingStatus(count) }}
          </div>
        </div>
      </div>
    </div>

    <!-- Data Import -->
    <div class="import-section">
      <div class="section-header">
        <h3>Data Import & Validation</h3>
      </div>
      
      <div class="import-panel">
        <div class="upload-area" @click="triggerFileUpload" @dragover.prevent @drop.prevent="handleDrop">
          <input 
            ref="fileInput" 
            type="file" 
            accept=".csv,.xlsx,.json" 
            @change="handleFileSelect"
            style="display: none"
          >
          <div class="upload-content">
            <div class="upload-icon">📁</div>
            <h4>Upload Data File</h4>
            <p>Drag and drop your file here or click to browse</p>
            <p class="upload-formats">Supported formats: CSV, Excel, JSON</p>
          </div>
        </div>

        <div v-if="selectedFile" class="file-info">
          <div class="file-details">
            <span class="file-name">{{ selectedFile.name }}</span>
            <span class="file-size">{{ formatFileSize(selectedFile.size) }}</span>
          </div>
          <button class="btn btn-primary" @click="validateFile" :disabled="validating">
            <i class="icon-check"></i>
            {{ validating ? 'Validating...' : 'Validate File' }}
          </button>
        </div>

        <div v-if="validationResult" class="validation-result">
          <div class="validation-header">
            <h4>Validation Results</h4>
            <div class="validation-status" :class="validationResult.valid ? 'valid' : 'invalid'">
              {{ validationResult.valid ? 'Valid' : 'Invalid' }}
            </div>
          </div>
          
          <div class="validation-details">
            <div class="quality-score-display">
              <span>Quality Score: </span>
              <span class="score" :class="getQualityScoreClass(validationResult.quality_score)">
                {{ validationResult.quality_score.toFixed(1) }}%
              </span>
            </div>
            
            <div v-if="validationResult.errors.length" class="errors">
              <h5>Errors:</h5>
              <ul>
                <li v-for="error in validationResult.errors" :key="error" class="error-item">
                  {{ error }}
                </li>
              </ul>
            </div>
            
            <div v-if="validationResult.warnings.length" class="warnings">
              <h5>Warnings:</h5>
              <ul>
                <li v-for="warning in validationResult.warnings" :key="warning" class="warning-item">
                  {{ warning }}
                </li>
              </ul>
            </div>
          </div>

          <div class="validation-actions">
            <button 
              class="btn btn-primary" 
              @click="importFile" 
              :disabled="!validationResult.valid || importing"
            >
              <i class="icon-upload"></i>
              {{ importing ? 'Importing...' : 'Import Data' }}
            </button>
            <button class="btn btn-secondary" @click="clearFile">
              <i class="icon-close"></i>
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Anomaly Detection -->
    <div class="anomaly-section">
      <div class="section-header">
        <h3>Anomaly Detection</h3>
        <button class="btn btn-secondary" @click="detectAnomalies" :disabled="detecting">
          <i class="icon-search"></i>
          {{ detecting ? 'Detecting...' : 'Run Detection' }}
        </button>
      </div>
      
      <div class="anomaly-content">
        <div class="anomaly-stats">
          <div class="anomaly-stat">
            <span class="stat-label">Detected Anomalies</span>
            <span class="stat-value">{{ dataQuality.anomaly_count }}</span>
          </div>
          <div class="anomaly-stat">
            <span class="stat-label">Detection Method</span>
            <span class="stat-value">Isolation Forest</span>
          </div>
          <div class="anomaly-stat">
            <span class="stat-label">Contamination</span>
            <span class="stat-value">10%</span>
          </div>
        </div>

        <div v-if="anomalies.length" class="anomalies-list">
          <h4>Recent Anomalies</h4>
          <div class="anomaly-item" v-for="anomaly in anomalies" :key="anomaly.id">
            <div class="anomaly-info">
              <div class="anomaly-time">{{ formatDate(anomaly.timestamp) }}</div>
              <div class="anomaly-description">{{ anomaly.description }}</div>
            </div>
            <div class="anomaly-severity" :class="anomaly.severity">
              {{ anomaly.severity }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Data Quality Rules -->
    <div class="rules-section">
      <div class="section-header">
        <h3>Data Quality Rules</h3>
        <button class="btn btn-primary" @click="addRule">
          <i class="icon-plus"></i>
          Add Rule
        </button>
      </div>
      
      <div class="rules-list">
        <div v-for="rule in qualityRules" :key="rule.id" class="rule-item">
          <div class="rule-info">
            <h4>{{ rule.name }}</h4>
            <p>{{ rule.description }}</p>
            <div class="rule-details">
              <span class="rule-column">Column: {{ rule.column }}</span>
              <span class="rule-condition">Condition: {{ rule.condition }}</span>
            </div>
          </div>
          <div class="rule-actions">
            <div class="rule-status" :class="rule.enabled ? 'enabled' : 'disabled'">
              {{ rule.enabled ? 'Enabled' : 'Disabled' }}
            </div>
            <button class="btn btn-sm btn-secondary" @click="editRule(rule)">
              Edit
            </button>
            <button class="btn btn-sm btn-danger" @click="deleteRule(rule.id)">
              Delete
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { toIsoLocalString } from '../utils/time';

// Reactive data
const dataQuality = ref({
  total_records: 0,
  missing_values: {},
  data_completeness: 0,
  anomaly_count: 0,
  quality_score: 0,
  last_updated: new Date()
});

const selectedFile = ref(null);
const validating = ref(false);
const importing = ref(false);
const detecting = ref(false);
const validationResult = ref(null);
const anomalies = ref([]);
const qualityRules = ref([]);

const fileInput = ref(null);

// Computed properties
const qualityScoreClass = computed(() => {
  const score = dataQuality.value.quality_score;
  if (score >= 90) return 'excellent';
  if (score >= 70) return 'good';
  if (score >= 50) return 'fair';
  return 'poor';
});

const totalMissingValues = computed(() => {
  return Object.values(dataQuality.value.missing_values).reduce((sum, count) => sum + count, 0);
});

const anomalyPercentage = computed(() => {
  if (dataQuality.value.total_records === 0) return 0;
  return (dataQuality.value.anomaly_count / dataQuality.value.total_records) * 100;
});

// Methods
const refreshData = async () => {
  try {
    const response = await fetch('/data/quality');
    const data = await response.json();
    dataQuality.value = data;
  } catch (error) {
    console.error('Failed to refresh data quality:', error);
  }
};

const getMissingStatus = (count) => {
  const percentage = (count / dataQuality.value.total_records) * 100;
  if (percentage === 0) return 'excellent';
  if (percentage < 5) return 'good';
  if (percentage < 15) return 'warning';
  return 'critical';
};

const getQualityScoreClass = (score) => {
  if (score >= 90) return 'excellent';
  if (score >= 70) return 'good';
  if (score >= 50) return 'fair';
  return 'poor';
};

const formatDate = (date) => {
  return toIsoLocalString(date) || date;
};

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const triggerFileUpload = () => {
  fileInput.value.click();
};

const handleFileSelect = (event) => {
  const file = event.target.files[0];
  if (file) {
    selectedFile.value = file;
  }
};

const handleDrop = (event) => {
  const files = event.dataTransfer.files;
  if (files.length > 0) {
    selectedFile.value = files[0];
  }
};

const validateFile = async () => {
  if (!selectedFile.value) return;

  validating.value = true;
  try {
    const formData = new FormData();
    formData.append('file', selectedFile.value);

    const response = await fetch('/data/import', {
      method: 'POST',
      body: formData
    });

    const result = await response.json();
    validationResult.value = {
      valid: result.status === 'completed',
      quality_score: result.quality_score,
      errors: result.errors || [],
      warnings: []
    };
  } catch (error) {
    console.error('File validation failed:', error);
    validationResult.value = {
      valid: false,
      quality_score: 0,
      errors: ['Validation failed: ' + error.message],
      warnings: []
    };
  } finally {
    validating.value = false;
  }
};

const importFile = async () => {
  if (!validationResult.value.valid) return;

  importing.value = true;
  try {
    // In a real implementation, this would trigger the actual import
    await new Promise(resolve => setTimeout(resolve, 2000)); // Simulate import
    alert('File imported successfully!');
    clearFile();
    refreshData();
  } catch (error) {
    console.error('File import failed:', error);
    alert('Import failed: ' + error.message);
  } finally {
    importing.value = false;
  }
};

const clearFile = () => {
  selectedFile.value = null;
  validationResult.value = null;
  if (fileInput.value) {
    fileInput.value.value = '';
  }
};

const detectAnomalies = async () => {
  detecting.value = true;
  try {
    // Simulate anomaly detection
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Mock anomalies
    anomalies.value = [
      {
        id: 1,
        timestamp: new Date(),
        description: 'Unusual energy spike detected',
        severity: 'high'
      },
      {
        id: 2,
        timestamp: new Date(Date.now() - 3600000),
        description: 'Temperature reading out of range',
        severity: 'medium'
      }
    ];
    
    refreshData();
  } catch (error) {
    console.error('Anomaly detection failed:', error);
  } finally {
    detecting.value = false;
  }
};

const addRule = () => {
  // In a real implementation, this would open a modal to add a new rule
  console.log('Add new quality rule');
};

const editRule = (rule) => {
  // In a real implementation, this would open a modal to edit the rule
  console.log('Edit rule:', rule);
};

const deleteRule = (ruleId) => {
  qualityRules.value = qualityRules.value.filter(rule => rule.id !== ruleId);
};

// Initialize data
onMounted(() => {
  refreshData();
  
  // Initialize quality rules
  qualityRules.value = [
    {
      id: 1,
      name: 'Energy Range Check',
      description: 'Energy values should be between 0 and 10000 Wh',
      column: 'Energy delta[Wh]',
      condition: '0 <= value <= 10000',
      enabled: true
    },
    {
      id: 2,
      name: 'Temperature Range Check',
      description: 'Temperature should be between -50 and 60°C',
      column: 'temp',
      condition: '-50 <= value <= 60',
      enabled: true
    },
    {
      id: 3,
      name: 'GHI Range Check',
      description: 'GHI should be between 0 and 1500 W/m²',
      column: 'GHI',
      condition: '0 <= value <= 1500',
      enabled: true
    }
  ];
});
</script>

<style scoped src="../styles/components/DataQuality.css"></style>
