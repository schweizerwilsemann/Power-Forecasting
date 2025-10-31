import { apiClient } from './apiClient';

export function useOperationsApi() {
  const fetchHistoricalAnalysis = async (payload) => {
    const { data } = await apiClient.post('/analysis/historical', payload);
    return data;
  };

  const fetchModelStatus = async () => {
    const { data } = await apiClient.get('/models/status');
    return data;
  };

  const triggerModelRetrain = async () => {
    const { data } = await apiClient.post('/models/retrain');
    return data;
  };

  return { fetchHistoricalAnalysis, fetchModelStatus, triggerModelRetrain };
}
